import random
import json
from urllib.parse import quote
from fastapi import UploadFile, File
from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import get_session
from models import Investigator, DiceLog

router = APIRouter(prefix="/investigators")
templates = Jinja2Templates(directory="templates")


# --- 新增：CoC 7版 判定逻辑 ---
def calculate_roll_result(target_val: int):
    dice = random.randint(1, 100)

    # CoC 7th Edition Rules
    # 1: 大成功 (Critical)
    # <= 1/5: 极难成功 (Extreme)
    # <= 1/2: 困难成功 (Hard)
    # <= target: 普通成功 (Regular)
    # > target: 失败 (Failure)
    # >= 96 (if target < 50) or 100 (if target >= 50): 大失败 (Fumble)

    result_type = "失败"
    color = "secondary"  # 灰色

    is_fumble = False
    if target_val < 50 and dice >= 96:
        is_fumble = True
    elif target_val >= 50 and dice == 100:
        is_fumble = True

    if is_fumble:
        result_type = "大失败"
        color = "dark"  # 或者黑色/深红
    elif dice == 1:
        result_type = "大成功"
        color = "success"  # 亮绿
    elif dice <= target_val // 5:
        result_type = "极难成功"
        color = "warning"  # 金色/橙色
    elif dice <= target_val // 2:
        result_type = "困难成功"
        color = "info"  # 蓝色
    elif dice <= target_val:
        result_type = "成功"
        color = "success"  # 绿色
    else:
        result_type = "失败"
        color = "danger"  # 红色

    return dice, result_type, color


# --- 新增：HTMX 掷骰接口 ---
@router.post("/roll_check", response_class=HTMLResponse)
async def roll_check(
        request: Request,
        response: Response,
        skill_name: str = Form(...),
        skill_val: int = Form(...),
        inv_name: str = Form(default="未命名"),
        session: Session = Depends(get_session)
):
    """
    接收技能名和技能值，返回一段 HTML 提示框
    """
    dice, result, color = calculate_roll_result(skill_val)

    # --- 保存日志 ---
    log_entry = DiceLog(
        investigator_name=inv_name,
        action_name=skill_name,
        result_text=f"{dice} / {skill_val} ({result})",
        result_color=color
    )
    session.add(log_entry)
    session.commit()

    # --- 关键：设置 HTMX 触发器 ---
    # 这告诉前端：有一个叫 'newDiceRoll' 的事件发生了
    response.headers["HX-Trigger"] = "newDiceRoll"

    # 返回一个 Bootstrap Alert，带有动画效果
    # 这里的 hx-swap-oob 可以不用，直接返回替换 target 容器的内容
    return f"""
    <div class="alert alert-{color} alert-dismissible fade show shadow border-2" role="alert" style="border-color: currentColor;">
        <h5 class="alert-heading"><i class="fas fa-dice"></i> {skill_name} 判定</h5>
        <hr>
        <div class="d-flex justify-content-between align-items-center">
            <span class="fs-4">🎲 <strong>{dice}</strong> / {skill_val}</span>
            <span class="badge bg-{color} fs-5">{result}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    """

@router.post("/roll_custom")
async def roll_custom(
    response: Response,
    sides: int = Form(...),
    inv_name: str = Form(default="通用"),
    session: Session = Depends(get_session)
):
    """
    接收面数，直接返回一个纯数字文本。
    """
    try:
        if sides < 1:
            return "ERR"
        result = random.randint(1, sides)
        # --- 保存日志 ---
        log_entry = DiceLog(
            investigator_name=inv_name,
            action_name=f"1d{sides}",
            result_text=str(result),
            result_color="info"  # 蓝色
        )
        session.add(log_entry)
        session.commit()

        # --- 设置 HTMX 触发器 ---
        response.headers["HX-Trigger"] = "newDiceRoll"
        return str(result)  # 直接返回字符串 "5", "12" 等
    except Exception:
        return "ERR"

# --- 新增：Inspection 页面路由 ---
@router.get("/inspect/{inv_id}", response_class=HTMLResponse)
async def inspect_view(request: Request, inv_id: int, session: Session = Depends(get_session)):
    inv = session.get(Investigator, inv_id)
    return templates.TemplateResponse("inspect.html", {"request": request, "inv": inv})


# --- 新增：Inspection 保存路由 (Stay on page) ---
@router.post("/save_status", response_class=HTMLResponse)
async def save_status(
        request: Request,
        session: Session = Depends(get_session)
):
    form_data = await request.form()
    data = dict(form_data)

    # 简单的处理空int逻辑 (同 save_investigator)
    for key, value in data.items():
        if value == "" and key in Investigator.__annotations__:
            if Investigator.__annotations__[key] == int:
                data[key] = 0

    inv_id = data.get("id")
    if inv_id:
        db_inv = session.get(Investigator, int(inv_id))
        if db_inv:
            # 这是一个部分更新，我们只更新表单里提交上来的字段
            # 因为 inspect 页面只有部分字段在 <form> 内，其他字段不会被提交
            # 所以不用担心覆盖掉名字等信息（只要它们不在 form 里或设为 readonly 且 name 传了）
            for key, value in data.items():
                if hasattr(db_inv, key):
                    setattr(db_inv, key, value)
            session.add(db_inv)
            session.commit()
            session.refresh(db_inv)

            status_text = f"HP:{db_inv.hp_current} MP:{db_inv.mp_current} SAN:{db_inv.san_current}"
            log_entry = DiceLog(
                investigator_name=db_inv.name,
                action_name="状态更新",  # 动作名
                result_text=status_text,  # 结果展示为当前数值
                result_color="primary"  # 蓝色，表示系统信息
            )
            session.add(log_entry)
            session.commit()

    # 重定向回 inspection 页面
    return RedirectResponse(url=f"/investigators/inspect/{inv_id}", status_code=303)

#调查员名单轮询同步更新专用
@router.get("/list/rows", response_class=HTMLResponse)
async def get_investigator_rows(request: Request, session: Session = Depends(get_session)):
    # 逻辑与首页列表一致，只是返回的模板不同
    statement = select(Investigator).where(Investigator.card_type == "player")
    results = session.exec(statement).all()
    return templates.TemplateResponse("snippets/investigator_rows.html", {"request": request, "investigators": results})

@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """显示创建空表单"""
    return templates.TemplateResponse("create.html", {"request": request, "inv": None})


@router.get("/edit/{inv_id}", response_class=HTMLResponse)
async def edit_form(request: Request, inv_id: int, session: Session = Depends(get_session)):
    """显示编辑表单，并在模板中填充数据"""
    inv = session.get(Investigator, inv_id)
    return templates.TemplateResponse("create.html", {"request": request, "inv": inv})


@router.post("/save", response_class=HTMLResponse)
async def save_investigator(
        request: Request,
        session: Session = Depends(get_session)
):
    """
    接收表单数据并保存/更新。
    因为字段太多，我们直接解析 request.form()
    """
    form_data = await request.form()
    data = dict(form_data)

    # 处理 checkbox 或空整数字段 (HTML表单空字符串转int会报错)
    # 这里做一个简单的清洗逻辑：如果模型定义是int但表单是空串，设为0
    for key, value in data.items():
        if value == "" and key in Investigator.__annotations__:
            if Investigator.__annotations__[key] == int:
                data[key] = 0

    # 判断是更新还是新建
    inv_id = data.get("id")
    if inv_id and inv_id != "None" and inv_id != "":
        # 更新逻辑
        db_inv = session.get(Investigator, int(inv_id))
        if db_inv:
            inv_data = Investigator(**data)  # 验证数据
            for key, value in data.items():
                setattr(db_inv, key, value)
            session.add(db_inv)
    else:
        # 新建逻辑
        if "id" in data: del data["id"]  # 移除空ID让数据库自动生成
        new_inv = Investigator(**data)
        session.add(new_inv)

    session.commit()

    # 保存后重定向回列表页 (符合 Post-Redirect-Get 模式)
    return RedirectResponse(url="/", status_code=303)


@router.get("/export_json/{inv_id}")
async def export_investigator_json(inv_id: int, session: Session = Depends(get_session)):
    """
    导出指定调查员为 JSON 文件
    """
    inv = session.get(Investigator, inv_id)
    if not inv:
        return Response("角色不存在", status_code=404)

    # 1. 转换为字典
    data = inv.model_dump()  # 如果 SQLModel 版本较老，可能需要用 .dict()

    # 2. 生成文件名 (URL编码防止中文乱码)
    filename = f"{inv.name}_{inv.occupation}.json"
    encoded_filename = quote(filename)

    # 3. 返回 JSON 文件流
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.post("/import_json")
async def import_investigator_json(
        file: UploadFile = File(...),
        session: Session = Depends(get_session)
):
    """
    上传 JSON 文件并导入为新角色
    """
    try:
        # 1. 读取并解析 JSON
        content = await file.read()
        data = json.loads(content)

        # 2. 清洗数据：移除 id (让数据库自动生成新ID)
        if "id" in data:
            del data["id"]

        # 3. 创建新对象 (利用 **data 解包)
        new_inv = Investigator(**data)

        # 4. 为了区分，可以在名字后面加个标记，或者直接存
        # new_inv.name = f"{new_inv.name} (导入)"

        session.add(new_inv)
        session.commit()

        # 5. 导入成功后回到列表页
        return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        return Response(f"导入失败: {str(e)}", status_code=400)