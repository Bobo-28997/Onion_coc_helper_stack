# routers/logs.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import get_session
from models import DiceLog
import csv
import io
from fastapi.responses import StreamingResponse # 用于流式下载文件

# 注意：prefix 设置为 "/logs"，tags 用于自动文档归类
router = APIRouter(prefix="/logs", tags=["logs"])
templates = Jinja2Templates(directory="templates")


@router.get("/latest", response_class=HTMLResponse)
async def get_latest_logs(request: Request, session: Session = Depends(get_session)):
    """
    获取最新的 40 条掷骰记录
    """
    # 按时间倒序查询
    statement = select(DiceLog).order_by(DiceLog.created_at.desc()).limit(40)
    logs = session.exec(statement).all()

    return templates.TemplateResponse("log_list.html", {"request": request, "logs": logs})

@router.post("/add_note", response_class=HTMLResponse)
async def add_note(
    request: Request,
    investigator_name: str = Form(...),
    note_content: str = Form(...), # 前端传来的笔记内容
    session: Session = Depends(get_session)
):
    """
    手动添加一条笔记日志
    """
    # 如果没填名字，给个默认值
    if not investigator_name:
        investigator_name = "KP"

    log_entry = DiceLog(
        investigator_name=investigator_name,
        action_name=note_content,      # 将笔记内容作为 action_name 显示在下方
        result_text="📝 笔记",         # 固定显示的提示文本
        result_color="secondary"       # 固定颜色（灰色），表示这是备注
    )
    session.add(log_entry)
    session.commit()

    # 提交完后，直接返回最新的日志列表，HTMX 会把侧边栏更新
    # 复用 get_latest_logs 的逻辑
    statement = select(DiceLog).order_by(DiceLog.created_at.desc()).limit(20)
    logs = session.exec(statement).all()
    return templates.TemplateResponse("log_list.html", {"request": request, "logs": logs})


@router.get("/export_csv")
async def export_logs_csv(session: Session = Depends(get_session)):
    """
    导出所有投骰日志为 CSV 文件
    """
    # 1. 查询所有日志 (按时间倒序)
    statement = select(DiceLog).order_by(DiceLog.created_at.desc())
    logs = session.exec(statement).all()

    # 2. 使用 StringIO 在内存中构建 CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 写表头
    writer.writerow(["ID", "时间", "调查员", "动作", "结果文本", "结果类型"])

    # 写数据
    for log in logs:
        writer.writerow([
            log.id,
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.investigator_name,
            log.action_name,
            log.result_text,
            log.result_color
        ])

    # 指针回到开头
    output.seek(0)

    # 3. 返回流式响应
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=coc_dice_logs.csv"}
    )
