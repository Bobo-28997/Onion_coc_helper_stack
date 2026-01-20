from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Investigator(SQLModel, table=True):
    # 0. 主键
    id: Optional[int] = Field(default=None, primary_key=True)

    # 1. 基础信息
    player_name: str = Field(default="")
    name: str = Field(default="")
    occupation: str = Field(default="")
    mother_tongue: str = Field(default="")
    gender: str = Field(default="")
    age: int = Field(default=20)

    # --- 新增字段 ---
    # 1. 队伍/分组 (用于 KP 面板分队，默认都叫'Alpha')
    team_name: str = Field(default="Alpha")

    # 2. 卡片类型 (player, npc, monster)
    card_type: str = Field(default="player")

    # 3. 怪物专属 (如果是怪物，可以使用 build_val 作为体格，这里增加护甲)
    armor: int = Field(default=0)

    # 2. 基本属性
    str_stat: int = Field(default=50)  # 力量
    dex_stat: int = Field(default=50)  # 敏捷
    con_stat: int = Field(default=50)  # 体质
    pow_stat: int = Field(default=50)  # 意志
    app_stat: int = Field(default=50)  # 外貌
    siz_stat: int = Field(default=50)  # 体型
    int_stat: int = Field(default=50)  # 智力
    edu_stat: int = Field(default=50)  # 教育
    luck_stat: int = Field(default=50)  # 幸运

    hp_max: int = Field(default=10)  # 生命上限
    mp_max: int = Field(default=10)  # 魔法上限
    db_val: str = Field(default="0")  # 伤害加值 (通常是字符串如 +1d4)
    build_stat: int = Field(default=0)

    # 3. 当前属性
    san_current: int = Field(default=50)
    mp_current: int = Field(default=10)
    hp_current: int = Field(default=10)

    # 4. 技能 (仅列举部分作为示例，实际开发需补全所有)
    # 技巧：使用 Field(alias="...") 可以在表单中使用中文name，但建议数据库字段用英文
    credit_rating: int = Field(default=0)
    spot_hidden: int = Field(default=25)
    listen: int = Field(default=20)
    library_use: int = Field(default=20)
    first_aid: int = Field(default=30)
    medicine: int = Field(default=1)  # 修正默认值
    psychoanalysis: int = Field(default=1)
    charm: int = Field(default=15)
    fast_talk: int = Field(default=5)
    intimidate: int = Field(default=15)
    persuade: int = Field(default=10)
    accounting: int = Field(default=5)
    appraise: int = Field(default=5)
    archaeology: int = Field(default=1)
    anthropology: int = Field(default=1)
    law: int = Field(default=5)
    history: int = Field(default=5)
    occult: int = Field(default=5)
    natural_world: int = Field(default=10)
    psychology: int = Field(default=10)
    science_a_name: str = Field(default="")
    science_a_val: int = Field(default=1)
    science_b_name: str = Field(default="")
    science_b_val: int = Field(default=1)
    science_c_name: str = Field(default="")
    science_c_val: int = Field(default=1)
    ride: int = Field(default=5)
    drive_auto: int = Field(default=20)
    drive_a_name: str = Field(default="")
    drive_a_val: int = Field(default=1)
    locksmith: int = Field(default=1)
    mech_repair: int = Field(default=10)
    elec_repair: int = Field(default=10)
    climb: int = Field(default=20)
    jump: int = Field(default=20)
    swim: int = Field(default=20)
    stealth: int = Field(default=20)
    track: int = Field(default=10)
    sleight_of_hand: int = Field(default=10)
    disguise: int = Field(default=5)
    navigate: int = Field(default=10)
    survival: int = Field(default=10)
    dodge: int = Field(default=25)
    throw: int = Field(default=20)
    fighting_brawl: int = Field(default=25)
    fighting_b_name: str = Field(default="")
    fighting_b_val: int = Field(default=1)
    fighting_c_name: str = Field(default="")
    fighting_c_val: int = Field(default=1)
    firearms_handgun: int = Field(default=25)
    firearms_rifle: int = Field(default=25)
    firearms_c_name: str = Field(default="")
    firearms_c_val: int = Field(default=1)
    language: int = Field(default=50)
    language_b_name: str = Field(default="")
    language_b_val: int = Field(default=1)
    language_c_name: str = Field(default="")
    language_c_val: int = Field(default=1)
    craft_a_name: str = Field(default="")
    craft_a_val: int = Field(default=5)
    craft_b_name: str = Field(default="")
    craft_b_val: int = Field(default=5)
    cthulhu_mythos: int = Field(default=0)

    # 5. 物品 (使用 item_1 到 item_8)
    item_1: str = Field(default="")
    item_2: str = Field(default="")
    item_3: str = Field(default="")
    item_4: str = Field(default="")
    item_5: str = Field(default="")
    item_6: str = Field(default="")
    item_7: str = Field(default="")
    item_8: str = Field(default="")

    # 6. 背景
    description: str = Field(default="")
    ideology: str = Field(default="")
    significant_people: str = Field(default="")
    significant_location: str = Field(default="")
    treasured_possession: str = Field(default="")
    traits: str = Field(default="")
    injuries: str = Field(default="")

    # 7. 经历 & 8. 法术 (使用大文本存储或拆分字段，这里简化处理)
    history_text_1: str = Field(default="")# 可以在前端用换行符分隔
    history_text_2: str = Field(default="")
    history_text_3: str = Field(default="")
    history_text_4: str = Field(default="")
    spells_text_1: str = Field(default="")
    spells_text_2: str = Field(default="")
    spells_text_3: str = Field(default="")
    spells_text_4: str = Field(default="")

    #9. 武器伤害
    fighting_damage_a: str = Field(default="")
    fighting_damage_b: str = Field(default="")
    fighting_damage_c: str = Field(default="")
    firearms_damage_a: str = Field(default="")
    firearms_damage_b: str = Field(default="")
    firearms_damage_c: str = Field(default="")

class DiceLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    investigator_name: str  # 记录是谁投的
    action_name: str        # 记录投了什么 (如 "侦查", "1d6")
    result_text: str        # 记录结果文本 (如 "55/60 成功")
    result_color: str       # 记录颜色 (success, danger, warning 等)
    created_at: datetime = Field(default_factory=datetime.now)
