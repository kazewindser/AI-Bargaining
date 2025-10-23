from otree.api import *
import random

doc = """
练习回合 - 1轮讨价还价博弈
让参与者熟悉实验流程
"""


class C(BaseConstants):
    NAME_IN_URL = 'human_human_Practice'
    PLAYERS_PER_GROUP = 2
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


def creating_session(subsession: Subsession):
    """为练习回合设置分组"""
    print("\n" + "=" * 70)
    print("🎯 开始练习回合分组")
    print("=" * 70)

    players = subsession.get_players()
    N = len(players)

    print(f"📊 总共有 {N} 个参与者")

    if N % 2 != 0:
        raise ValueError(f"参与者数量必须是偶数,当前为 {N} 人")

    # 随机分组
    player_indices = list(range(N))
    random.shuffle(player_indices)

    matrix = []
    print(f"\n{'=' * 60}")
    print(f"🎮 练习回合配对:")
    print(f"{'=' * 60}")
    print(f"  {'组号':<6} {'参与者A':<12} {'参与者B':<12} {'角色分配':<30}")
    print(f"  {'-' * 60}")

    for i in range(0, N, 2):
        p_a = players[player_indices[i]]
        p_b = players[player_indices[i + 1]]

        # 随机决定谁是P1,谁是P2
        if random.random() < 0.5:
            matrix.append([p_a, p_b])
            p_a.assigned_role = C.ROLE_P1
            p_b.assigned_role = C.ROLE_P2
            role_info = f"参与者{p_a.participant.id_in_session}=P1 | 参与者{p_b.participant.id_in_session}=P2"
        else:
            matrix.append([p_b, p_a])
            p_b.assigned_role = C.ROLE_P1
            p_a.assigned_role = C.ROLE_P2
            role_info = f"参与者{p_b.participant.id_in_session}=P1 | 参与者{p_a.participant.id_in_session}=P2"

        pair_num = (i // 2) + 1
        print(
            f"  第{pair_num}组  参与者{p_a.participant.id_in_session:<5}    参与者{p_b.participant.id_in_session:<5}    {role_info}")

    subsession.set_group_matrix(matrix)

    for g in subsession.get_groups():
        g.initial_proposer_id = 1

    print(f"\n✅ 练习回合分组完成,共 {len(matrix)} 组\n")
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
    initial_proposer_id = models.IntegerField(initial=1)


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


# ----------------- helpers -----------------
def get_discount_rate(stage: int, player_role: str) -> float:
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


def is_current_proposer(p: Player) -> bool:
    g: Group = p.group
    player_role = p.assigned_role
    return (player_role == g.proposer)


def respondent_role(g: Group) -> str:
    return C.ROLE_P2 if g.proposer == C.ROLE_P1 else C.ROLE_P1


def compute_payoffs_if_end(g: Group):
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

    p1 = g.get_player_by_id(1)
    p2 = g.get_player_by_id(2)

    if p1.role() == C.ROLE_P1:
        p1.payoff = cu(g.p1_discounted_points)
        p2.payoff = cu(g.p2_discounted_points)
    else:
        p1.payoff = cu(g.p2_discounted_points)
        p2.payoff = cu(g.p1_discounted_points)


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
        if g.finished or g.offer_locked:
            return False
        return is_current_proposer(p)

    @staticmethod
    def vars_for_template(p: Player):
        g: Group = p.group
        my_discount = round(get_discount_rate(g.stage, p.assigned_role), 2)
        p.offer_points = None

        return dict(
            stage=g.stage,
            endowment=C.ENDOWMENT,
            you=p.assigned_role,
            other=respondent_role(g),
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

        g.offer_locked = True
        p.accepted_offer = None


class WaitForOffer(WaitPage):
    title_text = "お待ちください"
    body_text = "相手からの提案を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        return (not g.finished) and (not g.offer_locked)


class Bargain_Respond(Page):
    form_model = 'player'
    form_fields = ['accepted_offer']

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or not g.offer_locked:
            return False
        return not is_current_proposer(p)

    @staticmethod
    def vars_for_template(p: Player):
        g: Group = p.group
        my_discount = round(get_discount_rate(g.stage, p.assigned_role), 2)

        return dict(
            stage=g.stage,
            offer=g.offer_points,
            you=p.assigned_role,
            other=g.proposer,
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

        if decision:
            g.accepted = True
            g.finished = True
            g.offer_locked = False
            compute_payoffs_if_end(g)
        else:
            g.accepted = False
            g.stage += 1

            if g.stage > C.MAX_STAGE:
                g.finished = True
                g.offer_locked = False
                compute_payoffs_if_end(g)
            else:
                g.proposer = respondent_role(g)
                g.offer_locked = False
                g.offer_points = 0

                for player in g.get_players():
                    player.offer_points = None
                    player.accepted_offer = None


class WaitAfterResponse(WaitPage):
    title_text = "お待ちください"
    body_text = "相手の応答を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        return (not g.finished) and g.offer_locked


# Stage 2
class Bargain_Propose_Stage2(Page):
    form_model = 'player'
    form_fields = ['offer_points']
    template_name = 'human_human_Practice/Bargain_Propose.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 2:
            return False
        return Bargain_Propose.is_displayed(p)

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Propose.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        if values['offer_points'] is None:
            return '手渡すポイントを入力してください / Please enter an offer'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Propose.before_next_page(p, timeout_happened)


class WaitForOffer_Stage2(WaitPage):
    title_text = "お待ちください"
    body_text = "提案が相手に拒否されました。相手からの提案を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 2:
            return False
        return WaitForOffer.is_displayed(p)


class Bargain_Respond_Stage2(Page):
    form_model = 'player'
    form_fields = ['accepted_offer']
    template_name = 'human_human_Practice/Bargain_Respond.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 2:
            return False
        return Bargain_Respond.is_displayed(p)

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Respond.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        if 'accepted_offer' not in values or values['accepted_offer'] is None:
            return '受け入れるか拒否するかを選択してください / Please select Accept or Reject'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Respond.before_next_page(p, timeout_happened)


class WaitAfterResponse_Stage2(WaitPage):
    title_text = "お待ちください"
    body_text = "相手の応答を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 2:
            return False
        return WaitAfterResponse.is_displayed(p)


# Stage 3
class Bargain_Propose_Stage3(Page):
    form_model = 'player'
    form_fields = ['offer_points']
    template_name = 'human_human_Practice/Bargain_Propose.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 3:
            return False
        return Bargain_Propose.is_displayed(p)

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Propose.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        if values['offer_points'] is None:
            return '手渡すポイントを入力してください / Please enter an offer'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Propose.before_next_page(p, timeout_happened)


class WaitForOffer_Stage3(WaitPage):
    title_text = "お待ちください"
    body_text = "提案が相手に拒否されました。相手からの提案を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 3:
            return False
        return WaitForOffer.is_displayed(p)


class Bargain_Respond_Stage3(Page):
    form_model = 'player'
    form_fields = ['accepted_offer']
    template_name = 'human_human_Practice/Bargain_Respond.html'

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 3:
            return False
        return Bargain_Respond.is_displayed(p)

    @staticmethod
    def vars_for_template(p: Player):
        return Bargain_Respond.vars_for_template(p)

    @staticmethod
    def error_message(p: Player, values):
        if 'accepted_offer' not in values or values['accepted_offer'] is None:
            return '受け入れるか拒否するかを選択してください / Please select Accept or Reject'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        return Bargain_Respond.before_next_page(p, timeout_happened)


class WaitAfterResponse_Stage3(WaitPage):
    title_text = "お待ちください"
    body_text = "相手の応答を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        if g.finished or g.stage < 3:
            return False
        return WaitAfterResponse.is_displayed(p)


class ResultsWait(WaitPage):
    title_text = "お待ちください"
    body_text = "結果待ちです..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        return g.finished is True


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
    WaitForOffer,
    Bargain_Respond,
    WaitAfterResponse,
    # Stage 2
    Bargain_Propose_Stage2,
    WaitForOffer_Stage2,
    Bargain_Respond_Stage2,
    WaitAfterResponse_Stage2,
    # Stage 3
    Bargain_Propose_Stage3,
    WaitForOffer_Stage3,
    Bargain_Respond_Stage3,
    WaitAfterResponse_Stage3,
    # Results
    ResultsWait,
    Results,
    WaitForPlayers
]