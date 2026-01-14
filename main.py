import random  # <--- 1. 补回缺失的 random
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select, Session

from database import create_db_and_tables, get_session
from models import Investigator
from routers import investigators, logs, kp


# 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 启动逻辑 ---
    create_db_and_tables()
    print("✅ 数据库表结构已初始化")
    yield
    # --- 关闭逻辑 ---
    print("🛑 应用已关闭")


app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(investigators.router)
app.include_router(logs.router)
app.include_router(kp.router)
# --- 页面路由 ---

@app.get("/", response_class=HTMLResponse)
async def list_investigators(request: Request, session: Session = Depends(get_session)):
    """首页：列出所有调查员"""
    statement = select(Investigator).where(Investigator.card_type == "player")
    results = session.exec(statement).all()
    return templates.TemplateResponse("list.html", {"request": request, "investigators": results})


@app.get("/tool/dice", response_class=HTMLResponse)
async def dice_tool(request: Request):
    """显示骰子工具页面"""
    # 确保你创建了 templates/dice.html
    return templates.TemplateResponse("dice.html", {"request": request})


# --- 功能接口 ---

# 2. 补回缺失的 SC 判定接口
@app.get("/roll/sc", response_class=HTMLResponse)
async def roll_sanity_check():
    """
    处理理智检定请求。
    """
    dice_result = random.randint(1, 100)

    result_text = f"投掷结果：{dice_result}"
    color = "black"
    if dice_result <= 5:
        result_text += " (大成功！)"
        color = "green"
    elif dice_result >= 96:
        result_text += " (大失败！)"
        color = "red"

    return f"""
    <div class="alert" style="color: {color}; border: 1px dashed {color}; margin-top: 1rem;">
        <strong>🎲 {result_text}</strong>
    </div>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)