# routers/kp.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import get_session
from models import Investigator, DiceLog
from routers.investigators import calculate_roll_result  # 复用之前的判定逻辑

router = APIRouter(prefix="/kp", tags=["kp"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def kp_dashboard(request: Request, session: Session = Depends(get_session)):
    """
    KP 帷幕：显示所有角色，按队伍分组，按敏捷排序（行动轮）
    """
    # 查询所有角色，先按队伍名排序，再按敏捷倒序（战斗轮顺序）
    statement = select(Investigator).order_by(Investigator.team_name, Investigator.dex_stat.desc())
    all_invs = session.exec(statement).all()

    # 在 Python 中进行分组处理，方便模板渲染
    teams = {}
    for inv in all_invs:
        if inv.team_name not in teams:
            teams[inv.team_name] = []
        teams[inv.team_name].append(inv)

    return templates.TemplateResponse("kp_dashboard.html", {
        "request": request,
        "teams": teams
    })


@router.post("/mass_roll", response_class=HTMLResponse)
async def mass_roll(
        team_name: str = Form(...),
        skill_key: str = Form(...),  # 例如 'listen', 'spot_hidden', 'san_current'
        skill_label: str = Form(...),  # 显示名称，例如 '聆听'
        session: Session = Depends(get_session)
):
    """
    一键暗投：为指定队伍的所有人投掷指定技能
    """
    statement = select(Investigator).where(Investigator.team_name == team_name)
    investigators = session.exec(statement).all()

    results = []

    for inv in investigators:
        # 动态获取属性值 (反射)
        val = getattr(inv, skill_key, 0)

        # 使用之前的逻辑计算结果
        dice, result_type, color = calculate_roll_result(val)

        # 记录结果
        results.append({
            "name": inv.name,
            "val": val,
            "dice": dice,
            "result": result_type,
            "color": color
        })

        # 写入日志 (KP暗投也可以记日志，或者你可以选择不记)
        log = DiceLog(
            investigator_name="KP(暗投)",
            action_name=f"{inv.name} 的 {skill_label}",
            result_text=f"{dice}/{val} {result_type}",
            result_color="secondary"
        )
        session.add(log)

    session.commit()

    # 返回一个 HTML 片段作为结果列表
    return templates.TemplateResponse("snippets/mass_roll_result.html", {
        "request": {},  # snippet 不需要完整 request
        "results": results,
        "skill_label": skill_label
    })


@router.post("/quick_change", response_class=HTMLResponse)
async def quick_change(
        inv_id: int = Form(...),
        field: str = Form(...),  # 'hp_current', 'mp_current', 'san_current'
        delta: int = Form(...),  # +1, -1, +5, -5
        session: Session = Depends(get_session)
):
    """
    快速加减血/蓝/理智
    """
    inv = session.get(Investigator, inv_id)
    if inv:
        current_val = getattr(inv, field)
        new_val = current_val + delta
        setattr(inv, field, new_val)
        session.add(inv)
        session.commit()

        # 返回新的数值字符串
        return str(new_val)
    return "Err"

@router.get("/dashboard/content", response_class=HTMLResponse)
async def kp_dashboard_content(request: Request, session: Session = Depends(get_session)):
    """只返回 KP 面板的队伍列表内容"""
    # 逻辑和 dashboard 接口一样，查询并分组
    statement = select(Investigator).order_by(Investigator.team_name, Investigator.dex_stat.desc())
    all_invs = session.exec(statement).all()

    teams = {}
    for inv in all_invs:
        if inv.team_name not in teams:
            teams[inv.team_name] = []
        teams[inv.team_name].append(inv)

    return templates.TemplateResponse("snippets/kp_dashboard_teams.html", {
        "request": request,
        "teams": teams
    })