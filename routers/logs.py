# routers/logs.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import get_session
from models import DiceLog

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

