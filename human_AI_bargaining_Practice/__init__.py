from otree.api import *
import random
import os


# 延迟导入 OpenAI,避免初始化时的导入错误
def get_openai_client():
    """获取 OpenAI 客户端"""
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            print("[OpenAI] Warning: OPENAI_API_KEY not set")
            return None
        return OpenAI(api_key=api_key)
    except Exception as e:
        print(f"[OpenAI] Failed to initialize client: {e}")
        return None


doc = """
练习回合 - 1轮与AI的讨价还价博弈
让参与者熟悉与AI对战的实验流程
"""


class C(BaseConstants):
    NAME_IN_URL = 'human_AI_bargaining_Practice'
    PLAYERS_PER_GROUP = None  # 单人组,对手为AI
    NUM_ROUNDS = 1  # 只有1轮练习
    ENDOWMENT = 100
    ROLE_P1 = 'P1'
    ROLE_P2 = 'P2'
    MAX_STAGE = 3

    # 折扣率设置
    DISCOUNT_P1 = 0.6
    DISCOUNT_P2 = 0.4


class Subsession(BaseSubsession):
    pass


# ========== 10轮正式版本的 creating_session ==========
def creating_session(subsession: Subsession):
    """在 session 创建时随机分配角色，但确保每轮 P1 和 P2 数量平衡"""

    players = subsession.get_players()
    matrix = [[p] for p in players]  # 每个玩家一个独立的组
    subsession.set_group_matrix(matrix)

    if subsession.round_number == 1:
        import sys

        sys.stderr.write("\n" + "=" * 70 + "\n")
        sys.stderr.write("🔴 T2 Treatment: 为每位玩家随机分配角色（平衡分配）\n")
        sys.stderr.write("=" * 70 + "\n")
        sys.stderr.flush()

        print("\n" + "=" * 70)
        print("🔴 T2 Treatment: 为每位玩家随机分配角色（平衡分配）")
        print("=" * 70)

        # 获取第一轮的所有玩家
        players_r1 = subsession.get_players()
        N = len(players_r1)

        print(f"📊 总共有 {N} 个参与者")

        # 为每一轮分配角色
        for round_num in range(1, C.NUM_ROUNDS + 1):
            current_subsession = subsession.in_round(round_num)
            round_players = current_subsession.get_players()

            # 🔴 新增：平衡角色分配
            num_players = len(round_players)
            num_p1 = num_players // 2  # 一半是 P1
            num_p2 = num_players - num_p1  # 剩下的是 P2

            # 创建角色列表：一半 P1，一半 P2
            roles = [C.ROLE_P1] * num_p1 + [C.ROLE_P2] * num_p2

            # 随机打乱角色列表
            random.shuffle(roles)

            print(f"\n--- Round {round_num} ---")
            print(f"角色分配: {num_p1} 个 P1, {num_p2} 个 P2")

            # 分配角色给玩家
            for i, p in enumerate(round_players):
                role = roles[i]
                p.assigned_role = role


                role_desc = "P1(提议)" if role == C.ROLE_P1 else "P2(回应)"
                print(f"  参与者{p.participant.id_in_session:<5}    {role_desc}")

                g = p.group
                if g:
                    g.stage = 1
                    g.proposer = C.ROLE_P1
                    g.finished = False
                    g.offer_locked = False
                    g.accepted = False
                    g.offer_points = 0
                    g.p1_points = 0
                    g.p2_points = 0
                    g.p1_discounted_points = 0
                    g.p2_discounted_points = 0
                    g.ai_offer = 0
                    g.ai_accepted = False


# ========== 练习版本的 creating_session ==========
def creating_session_practice(subsession: Subsession):
    """为练习回合随机分配角色（平衡分配）"""
    print("\n" + "=" * 70)
    print("🎯 AI练习回合: 为每位玩家随机分配角色（平衡分配）")
    print("=" * 70)

    players = subsession.get_players()
    matrix = [[p] for p in players]  # 每个玩家一个独立的组
    subsession.set_group_matrix(matrix)

    # 🔴 平衡角色分配
    num_players = len(players)
    num_p1 = num_players // 2  # 一半是 P1
    num_p2 = num_players - num_p1  # 剩下的是 P2

    print(f"📊 总共有 {num_players} 个参与者")
    print(f"角色分配: {num_p1} 个 P1, {num_p2} 个 P2")

    # 创建角色列表：一半 P1，一半 P2
    roles = [C.ROLE_P1] * num_p1 + [C.ROLE_P2] * num_p2

    # 随机打乱角色列表
    random.shuffle(roles)

    # 分配角色给玩家
    for i, p in enumerate(players):
        role = roles[i]
        p.assigned_role = role

        role_desc = "P1(提议)" if role == C.ROLE_P1 else "P2(回应)"
        print(f"  参与者{p.participant.id_in_session:<5}    {role_desc}")

        g = p.group
        if g:
            g.stage = 1
            g.proposer = C.ROLE_P1
            g.finished = False
            g.offer_locked = False
            g.accepted = False
            g.offer_points = 0
            g.p1_points = 0
            g.p2_points = 0
            g.p1_discounted_points = 0
            g.p2_discounted_points = 0
            g.ai_offer = 0
            g.ai_accepted = False

    print("✅ AI练习回合分配完成\n")
    print("=" * 70 + "\n")

class Group(BaseGroup):
    stage = models.IntegerField(initial=1)
    proposer = models.StringField(initial=C.ROLE_P1)
    finished = models.BooleanField(initial=False)
    offer_locked = models.BooleanField(initial=False)
    accepted = models.BooleanField(initial=False)
    offer_points = models.IntegerField(initial=0, min=0, max=C.ENDOWMENT)

    p1_points = models.IntegerField(initial=0)
    p2_points = models.IntegerField(initial=0)
    p1_discounted_points = models.FloatField(initial=0)
    p2_discounted_points = models.FloatField(initial=0)

    # AI 相关字段
    ai_offer = models.IntegerField(initial=0, min=0, max=C.ENDOWMENT)
    ai_accepted = models.BooleanField(initial=False)

    # 历史记录字段
    history_json = models.LongStringField(initial='[]')


class Player(BasePlayer):
    assigned_role = models.StringField(initial='P1')

    offer_points = models.IntegerField(
        min=0,
        max=C.ENDOWMENT,
        blank=True,
        label="手渡すポイント(0-100)"
    )

    accepted_offer = models.BooleanField(
        choices=[[True, '受け入れる / Accept'], [False, '拒否する / Reject']],
        widget=widgets.RadioSelect,
        blank=True,
        label="あなたの選択"
    )

    def role(self):
        return self.assigned_role


# ----------------- AI Logic -----------------

def get_history_from_group(g: Group) -> list:
    """从Group获取历史记录"""
    import json
    try:
        return json.loads(g.history_json) if g.history_json else []
    except:
        return []


def add_history_entry(g: Group, stage: int, proposer: str, offer: int, accepted: bool):
    """添加历史记录条目"""
    import json
    history = get_history_from_group(g)
    history.append({
        'stage': stage,
        'proposer': proposer,
        'offer': offer,
        'accepted': accepted
    })
    g.history_json = json.dumps(history)


def format_history_for_ai(history: list) -> str:
    """将历史记录格式化为人类可读的文本"""
    if not history:
        return "No previous offers in this round."

    lines = []
    for entry in history:
        stage = entry['stage']
        proposer = entry['proposer']
        offer = entry['offer']
        accepted = entry['accepted']
        status = "ACCEPTED" if accepted else "REJECTED"
        lines.append(f"Stage {stage}: {proposer} offered {offer} points → {status}")

    return "\n".join(lines)


def ai_propose(stage: int, ai_role: str, history: list = None) -> int:
    """使用ChatGPT API决定AI的提议"""
    client = get_openai_client()

    if client is None:
        fallback_offer = random.randint(40, 60)
        print(f"[ai_propose] Using fallback offer: {fallback_offer}")
        return fallback_offer

    discount_rate = get_discount_rate(stage, ai_role)
    opponent_role = C.ROLE_P2 if ai_role == C.ROLE_P1 else C.ROLE_P1
    opponent_discount = get_discount_rate(stage, opponent_role)

    history_text = format_history_for_ai(history or [])

    prompt = f"""You are the proposer in a 3-stage alternating-offers bargaining game over {C.ENDOWMENT} points.
Goal: maximize your own discounted payoff. Your opponent is human。

- Total points to divide: {C.ENDOWMENT}
- Your role: {ai_role}
- Current stage: {stage} out of {C.MAX_STAGE}
- Your discount rate at this stage: {discount_rate}
- Opponent's discount rate: {opponent_discount}

Previous negotiation history in this round:
{history_text}

Rules:
- You propose how many points to give to your opponent (0-{C.ENDOWMENT})
- You keep the remaining points
- If the offer is rejected, the game moves to the next stage with higher discounts
- If this is stage {C.MAX_STAGE}, this is the last chance to make a deal

Based on the negotiation history and current situation, what points would you offer to your opponent? 
Please respond with ONLY a number between 0 and {C.ENDOWMENT}."""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a strategic bargaining game AI. Respond only with a number."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            max_tokens=10
        )

        offer = int(response.choices[0].message.content.strip())
        offer = max(0, min(C.ENDOWMENT, offer))

        print(f"[ai_propose] AI (Role={ai_role}, Stage={stage}) proposes: {offer}")
        return offer

    except Exception as e:
        print(f"[ai_propose] API Error: {e}")
        fallback_offer = random.randint(40, 60)
        print(f"[ai_propose] Using fallback offer: {fallback_offer}")
        return fallback_offer


def ai_respond(offer: int, stage: int, ai_role: str, history: list = None) -> bool:
    """使用ChatGPT API决定AI是否接受提议"""
    client = get_openai_client()

    if client is None:
        discount_rate = get_discount_rate(stage, ai_role)
        discounted_offer = offer * discount_rate
        threshold = 35 if stage == 1 else (25 if stage == 2 else 15)
        return discounted_offer >= threshold

    discount_rate = get_discount_rate(stage, ai_role)
    discounted_offer = offer * discount_rate
    opponent_role = C.ROLE_P2 if ai_role == C.ROLE_P1 else C.ROLE_P1
    opponent_discount = get_discount_rate(stage, opponent_role)

    history_text = format_history_for_ai(history or [])

    next_stage_info = ""
    if stage < C.MAX_STAGE:
        next_discount = get_discount_rate(stage + 1, ai_role)
        next_stage_info = f"\n- If you reject, the game moves to stage {stage + 1}, where your discount rate would be {next_discount}"
    else:
        next_stage_info = f"\n- This is the FINAL stage. If you reject, both players get 0 points."

    prompt = f"""You are playing a 3-stage alternating-offers bargaining game. Here's the situation:
    
- Total points: {C.ENDOWMENT}
- Your role: {ai_role}
- Current stage: {stage} out of {C.MAX_STAGE}
- Offer you received: {offer} points
- Your discount rate: {discount_rate}
- Opponent's discount rate: {opponent_discount}
- Your discounted value if you accept: {discounted_offer:.2f} points{next_stage_info}

Previous negotiation history in this round:
{history_text}

Should you ACCEPT or REJECT this offer? Consider:
1. The discounted value you would receive now
2. The risk of getting worse terms (or zero) if negotiations continue
3. Strategic considerations based on the stage and negotiation history
4. Whether the opponent is making concessions or becoming more aggressive

Respond with ONLY one word: ACCEPT or REJECT"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system",
                 "content": "You are a strategic bargaining game AI. Respond only with ACCEPT or REJECT."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            max_tokens=10
        )

        decision_text = response.choices[0].message.content.strip().upper()
        decision = "ACCEPT" in decision_text

        print(f"[ai_respond] AI (Role={ai_role}, Stage={stage}) "
              f"{'ACCEPTS' if decision else 'REJECTS'} offer of {offer}")
        return decision
    except Exception as e:
        print(f"[ai_respond] API Error: {e}")
        threshold = 35 if stage == 1 else (25 if stage == 2 else 15)
        fallback_decision = discounted_offer >= threshold
        print(f"[ai_respond] Using fallback decision: {'ACCEPT' if fallback_decision else 'REJECT'}")
        return fallback_decision


# ----------------- helpers -----------------

def get_discount_rate(stage: int, player_role: str) -> float:
    """获取指定阶段和玩家角色的折扣率"""
    if stage == 1:
        return 1.0
    elif stage == 2:
        if player_role == C.ROLE_P1:
            return C.DISCOUNT_P1
        else:
            return C.DISCOUNT_P2
    else:
        if player_role == C.ROLE_P1:
            return C.DISCOUNT_P1 ** 2
        else:
            return C.DISCOUNT_P2 ** 2


def is_human_turn_to_propose(p: Player) -> bool:
    """判断是否轮到人类玩家提议"""
    g: Group = p.group
    return p.assigned_role == g.proposer


def get_ai_role(human_role: str) -> str:
    """获取AI的角色(与人类相反)"""
    return C.ROLE_P2 if human_role == C.ROLE_P1 else C.ROLE_P1


def compute_payoffs_if_end(g: Group, p: Player):
    """计算到group字段 + 玩家payoff(本轮)"""
    if g.accepted:
        if g.proposer == C.ROLE_P1:
            g.p1_points = C.ENDOWMENT - g.offer_points
            g.p2_points = g.offer_points
        else:
            g.p1_points = g.offer_points
            g.p2_points = C.ENDOWMENT - g.offer_points
    else:
        g.p1_points = 0
        g.p2_points = 0

    discount_p1 = get_discount_rate(g.stage, C.ROLE_P1)
    discount_p2 = get_discount_rate(g.stage, C.ROLE_P2)

    g.p1_discounted_points = g.p1_points * discount_p1
    g.p2_discounted_points = g.p2_points * discount_p2

    if p.assigned_role == C.ROLE_P1:
        p.payoff = cu(g.p1_discounted_points)
    else:
        p.payoff = cu(g.p2_discounted_points)


# ----------------- pages -----------------
class Start(Page):
    pass

class Intro(Page):
    @staticmethod
    def vars_for_template(p: Player):
        return dict(
            endowment=C.ENDOWMENT,
            max_stage=C.MAX_STAGE,
        )


class Bargain_Propose(Page):
    form_model = 'player'
    form_fields = ['offer_points']

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished:
            return False
        is_stage1 = (g.stage == 1)
        is_human_proposer = is_human_turn_to_propose(p)
        return is_stage1 and is_human_proposer

    @staticmethod
    def vars_for_template(p: Player):
        g: Group = p.group
        my_discount = round(get_discount_rate(g.stage, p.assigned_role), 2)
        ai_role = get_ai_role(p.assigned_role)
        p.offer_points = None

        return dict(
            stage=g.stage,
            endowment=C.ENDOWMENT,
            you=p.assigned_role,
            other=ai_role,
            my_discount=my_discount,
        )

    @staticmethod
    def error_message(p: Player, values):
        if values['offer_points'] is None:
            return '手渡すポイントを入力してください / Please enter an offer'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        g: Group = p.group
        offer = p.field_maybe_none('offer_points')

        if timeout_happened or offer is None:
            g.offer_points = 0
        else:
            g.offer_points = offer

        history = get_history_from_group(g)
        ai_role = get_ai_role(p.assigned_role)
        ai_decision = ai_respond(g.offer_points, g.stage, ai_role, history)

        add_history_entry(g, g.stage, p.assigned_role, g.offer_points, ai_decision)

        if ai_decision:
            g.accepted = True
            g.ai_accepted = True
            g.finished = True
            compute_payoffs_if_end(g, p)
        else:
            g.accepted = False
            g.ai_accepted = False
            g.stage += 1

            if g.stage > C.MAX_STAGE:
                g.finished = True
                compute_payoffs_if_end(g, p)
            else:
                g.proposer = ai_role
                g.offer_points = 0
                p.offer_points = None
                p.accepted_offer = None


class Bargain_Respond(Page):
    form_model = 'player'
    form_fields = ['accepted_offer']

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished:
            return False
        is_ai_proposer = (p.assigned_role != g.proposer)
        is_stage1 = (g.stage == 1)
        return is_stage1 and is_ai_proposer

    @staticmethod
    def vars_for_template(p: Player):
        g: Group = p.group
        history = get_history_from_group(g)
        ai_role = get_ai_role(p.assigned_role)
        ai_offer = ai_propose(g.stage, ai_role, history)
        g.ai_offer = ai_offer
        g.offer_points = ai_offer

        my_discount = round(get_discount_rate(g.stage, p.assigned_role), 2)
        p.accepted_offer = None

        return dict(
            stage=g.stage,
            offer=ai_offer,
            you=p.assigned_role,
            other=ai_role,
            endowment=C.ENDOWMENT,
            my_discount=my_discount,
        )

    @staticmethod
    def error_message(p: Player, values):
        if 'accepted_offer' not in values or values['accepted_offer'] is None:
            return '受け入れるか拒否するかを選択してください / Please select Accept or Reject'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        g: Group = p.group
        accepted_value = p.field_maybe_none('accepted_offer')

        if timeout_happened or accepted_value is None:
            decision = False
        else:
            decision = accepted_value

        ai_role = get_ai_role(p.assigned_role)
        add_history_entry(g, g.stage, ai_role, g.offer_points, decision)

        if decision:
            g.accepted = True
            g.finished = True
            compute_payoffs_if_end(g, p)
        else:
            g.accepted = False
            g.stage += 1

            if g.stage > C.MAX_STAGE:
                g.finished = True
                compute_payoffs_if_end(g, p)
            else:
                g.proposer = p.assigned_role
                g.offer_points = 0
                p.offer_points = None
                p.accepted_offer = None


# Stage 2
class Bargain_Propose_Stage2(Page):
    form_model = 'player'
    form_fields = ['offer_points']
    template_name = 'human_AI_bargaining_Practice/Bargain_Propose.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage != 2:
            return False
        return is_human_turn_to_propose(p)

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Propose.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        return Bargain_Propose.error_message(p, values)

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Propose.before_next_page(p, timeout_happened)


class Bargain_Respond_Stage2(Page):
    form_model = 'player'
    form_fields = ['accepted_offer']
    template_name = 'human_AI_bargaining_Practice/Bargain_Respond.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage != 2:
            return False
        is_ai_proposer = (p.assigned_role != g.proposer)
        return is_ai_proposer

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Respond.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        return Bargain_Respond.error_message(p, values)

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Respond.before_next_page(p, timeout_happened)


# Stage 3
class Bargain_Propose_Stage3(Page):
    form_model = 'player'
    form_fields = ['offer_points']
    template_name = 'human_AI_bargaining_Practice/Bargain_Propose.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage != 3:
            return False
        return is_human_turn_to_propose(p)

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Propose.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        return Bargain_Propose.error_message(p, values)

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Propose.before_next_page(p, timeout_happened)


class Bargain_Respond_Stage3(Page):
    form_model = 'player'
    form_fields = ['accepted_offer']
    template_name = 'human_AI_bargaining_Practice/Bargain_Respond.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage != 3:
            return False
        is_ai_proposer = (p.assigned_role != g.proposer)
        return is_ai_proposer

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Respond.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        return Bargain_Respond.error_message(p, values)

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Respond.before_next_page(p, timeout_happened)


class Results(Page):
    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        return g.finished is True

    @staticmethod
    def vars_for_template(p: Player):
        g: Group = p.group

        if p.assigned_role == C.ROLE_P1:
            my_discounted_points = g.p1_discounted_points
            my_original_points = g.p1_points
        else:
            my_discounted_points = g.p2_discounted_points
            my_original_points = g.p2_points

        is_proposer = (p.assigned_role == g.proposer)

        if g.accepted:
            if is_proposer:
                my_points_text = f"{C.ENDOWMENT} − {g.offer_points} = {C.ENDOWMENT - g.offer_points}"
            else:
                my_points_text = str(g.offer_points)
        else:
            my_points_text = "0"

        return dict(
            accepted=g.accepted,
            stage=g.stage,
            proposer=g.proposer,
            offer=g.offer_points,
            my_role=p.assigned_role,
            is_proposer=is_proposer,
            my_original_points=my_original_points,
            my_points_text=my_points_text,
            my_payoff=round(my_discounted_points, 2),
        )

class WaitForPlayers(WaitPage):
    """等待所有玩家完成所有轮次后再显示最终结果"""

    title_text = "お待ちください"
    body_text = "全ての参加者が練習ラウンドを終了するのを待っています..."
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        pass

page_sequence = [
   Start,
   Intro,
    # Stage 1
    Bargain_Propose,
    Bargain_Respond,
    # Stage 2
    Bargain_Propose_Stage2,
    Bargain_Respond_Stage2,
    # Stage 3
    Bargain_Propose_Stage3,
    Bargain_Respond_Stage3,
    # Results
    Results,
    WaitForPlayers
]