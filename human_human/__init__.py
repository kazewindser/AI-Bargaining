from otree.api import *
import re
from otree.api import *
import re

doc = """
Alternating-offer bargaining with T1 treatment only (human vs human).
12 players in T1; 2-player groups; 10 rounds using round-robin pairing.
"""


class C(BaseConstants):
    NAME_IN_URL = 'human_vs_human'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10  # 10轮
    ENDOWMENT = 100
    ROLE_P1 = 'P1'
    ROLE_P2 = 'P2'
    MAX_STAGE = 3

    # treatment 相关常量 - 只保留T1
    TREATMENT_NAMES = ['T1']
    PLAYERS_PER_TREATMENT = 4  # 根据您的实际参与人数调整

    # 折扣率设置
    DISCOUNT_P1 = 0.6  # P1每阶段的折扣率
    DISCOUNT_P2 = 0.4  # P2每阶段的折扣率

    # 最终支付倍数
    PAYMENT_MULTIPLIER = 30


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    """在 session 创建时统一设置所有轮次的分组"""
    
    # 只在第一轮执行分组逻辑
    if subsession.round_number == 1:
        import sys
        import random
        
        sys.stderr.write("\n" + "="*70 + "\n")
        sys.stderr.write("🔴 开始生成随机配对表\n")
        sys.stderr.write("="*70 + "\n")
        sys.stderr.flush()
        
        print("\n" + "="*70)
        print("🔴 开始生成随机配对表")
        print("="*70)
        
        # 获取第一轮的所有玩家
        players_r1 = subsession.get_players()
        N = len(players_r1)
        
        print(f"📊 总共有 {N} 个参与者")
        
        if N % 2 != 0:
            raise ValueError(f"参与者数量必须是偶数，当前为 {N} 人")
        
        # 🔴 生成随机配对表
        def generate_random_pairings(n, total_rounds):
            """为每一轮生成随机配对
            
            Args:
                n: 玩家总数（必须是偶数）
                total_rounds: 总轮数
            
            Returns:
                list of rounds, 每轮包含 n//2 个配对元组
            """
            all_rounds = []
            
            for round_num in range(total_rounds):
                # 创建玩家索引列表并随机打乱
                player_indices = list(range(n))
                random.shuffle(player_indices)
                
                # 相邻两个配对
                round_pairs = []
                for i in range(0, n, 2):
                    round_pairs.append((player_indices[i], player_indices[i+1]))
                
                all_rounds.append(round_pairs)
                
                print(f"   第{round_num+1}轮随机配对: {round_pairs}")
            
            return all_rounds
        
        # 生成所有轮次的随机配对
        random_schedule = generate_random_pairings(N, C.NUM_ROUNDS)
        
        print(f"\n✅ 生成了 {len(random_schedule)} 轮随机配对")

        # ===== 设置所有轮次的分组 =====
        for round_num in range(1, C.NUM_ROUNDS + 1):
            current_subsession = subsession.in_round(round_num)
            round_players = current_subsession.get_players()
            player_map = {p.participant.id_in_session: p for p in round_players}
            
            matrix = []
            
            print(f"\n{'='*60}")
            print(f"🎮 第 {round_num} 轮配对:")
            print(f"{'='*60}")
            
            # 使用随机配对表
            round_idx = round_num - 1  # 轮次从1开始，索引从0开始
            pairs = random_schedule[round_idx]
            
            print(f"  📋 第 {round_num} 轮配对方案:")
            print(f"  {'组号':<6} {'参与者A':<12} {'参与者B':<12} {'角色分配':<30}")
            print(f"  {'-'*60}")
            
            for pair_num, (idx_a, idx_b) in enumerate(pairs, 1):
                pid_a = players_r1[idx_a].participant.id_in_session
                pid_b = players_r1[idx_b].participant.id_in_session
                
                p_a = player_map[pid_a]
                p_b = player_map[pid_b]
                
                # 🔴 随机决定谁是 P1，谁是 P2
                if random.random() < 0.5:
                    # p_a 是 P1, p_b 是 P2
                    matrix.append([p_a, p_b])
                    p_a.assigned_role = C.ROLE_P1
                    p_b.assigned_role = C.ROLE_P2
                    role_info = f"参与者{pid_a}=角色P1(提议) | 参与者{pid_b}=角色P2(回应)"
                else:
                    # p_b 是 P1, p_a 是 P2
                    matrix.append([p_b, p_a])
                    p_b.assigned_role = C.ROLE_P1
                    p_a.assigned_role = C.ROLE_P2
                    role_info = f"参与者{pid_b}=角色P1(提议) | 参与者{pid_a}=角色P2(回应)"
                
                print(f"  第{pair_num}组  参与者{pid_a:<5}    参与者{pid_b:<5}    {role_info}")

            # 设置分组矩阵
            current_subsession.set_group_matrix(matrix)
            
            for g in current_subsession.get_groups():
                g.initial_proposer_id = 1

            print(f"\n  ✓ 第 {round_num} 轮分组矩阵设置完成，共 {len(matrix)} 组\n")

        print("\n" + "=" * 70)
        print("🎉 所有轮次的分组矩阵设置完成")
        print("=" * 70 + "\n")


class Group(BaseGroup):
    # 每轮初始化的状态
    stage = models.IntegerField(initial=1)  # 1..C.MAX_STAGE
    proposer = models.StringField(initial=C.ROLE_P1)  # 'P1' or 'P2'
    finished = models.BooleanField(initial=False)
    offer_locked = models.BooleanField(initial=False)
    accepted = models.BooleanField(initial=False)
    offer_points = models.IntegerField(initial=0, min=0, max=C.ENDOWMENT)

    # 原始点数（未折扣）
    p1_points = models.IntegerField(initial=0)
    p2_points = models.IntegerField(initial=0)

    # 折扣后的点数
    p1_discounted_points = models.FloatField(initial=0)
    p2_discounted_points = models.FloatField(initial=0)

    initial_proposer_id = models.IntegerField(initial=1)


class Player(BasePlayer):
    treatment = models.StringField(initial='T1')
    assigned_role = models.StringField(initial='P1')

    offer_points = models.IntegerField(
        min=0,
        max=C.ENDOWMENT,
        blank=True,
        label="応答者に提案する点数（0-100）"
    )

    accepted_offer = models.BooleanField(
        choices=[[True, '受け入れる / Accept'], [False, '拒否する / Reject']],
        widget=widgets.RadioSelect,
        blank=True,
        label="あなたの選択"
    )

    stage_1_offer = models.IntegerField(blank=True, initial=None)
    stage_2_offer = models.IntegerField(blank=True, initial=None)
    stage_3_offer = models.IntegerField(blank=True, initial=None)

    #  新增字段：记录每个stage的回应
    stage_1_accepted = models.BooleanField(blank=True, initial=None)
    stage_2_accepted = models.BooleanField(blank=True, initial=None)
    stage_3_accepted = models.BooleanField(blank=True, initial=None)

    def role(self):
        """返回玩家的固定角色（在本轮中不变）"""
        return self.assigned_role

    def role(self):
        """返回玩家的固定角色（在本轮中不变）"""
        return self.assigned_role

    def opponent_id(self):
        """返回对手的 participant id"""
        group_players = self.group.get_players()
        for p in group_players:
            if p.id_in_group != self.id_in_group:
                return p.participant.id_in_session
        return None

    def my_role_in_round(self):
        """返回当前轮次的角色（用于数据验证）"""
        return self.role()



   # 添加以下自定义方法用于数据导出
    def custom_export_stage1_proposer(self):
            """Stage 1 的提议者角色"""
            return self.group.initial_proposer_id == 1 and self.id_in_group == 1 or \
                self.group.initial_proposer_id == 2 and self.id_in_group == 2

    def custom_export_my_stage1_offer(self):
            """我在 Stage 1 提出的 offer（如果我是提议者）"""
            g = self.group
            if g.stage >= 1:
                # 检查 Stage 1 时我是否是提议者
                if self.assigned_role == C.ROLE_P1:  # 初始提议者
                    return self.stage_1_offer
            return None

    def custom_export_my_stage2_offer(self):
            """我在 Stage 2 提出的 offer（如果我是提议者）"""
            g = self.group
            if g.stage >= 2:
                # Stage 2 提议者是 P2
                if self.assigned_role == C.ROLE_P2:
                    return self.stage_2_offer
            return None

    def custom_export_my_stage3_offer(self):
            """我在 Stage 3 提出的 offer（如果我是提议者）"""
            g = self.group
            if g.stage >= 3:
                # Stage 3 提议者是 P1
                if self.assigned_role == C.ROLE_P1:
                    return self.stage_3_offer
            return None


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
    else:  # stage == 3
        if player_role == C.ROLE_P1:
            return C.DISCOUNT_P1 ** 2
        else:
            return C.DISCOUNT_P2 ** 2


def is_current_proposer(p: Player) -> bool:
    """判断玩家是否是当前阶段的提议者"""
    g: Group = p.group
    player_role = p.assigned_role

    result = (player_role == g.proposer)
    print(f"[is_current_proposer] Player {p.participant.id_in_session}: "
          f"player_role={player_role}, group.proposer={g.proposer}, result={result}")

    return result


def respondent_role(g: Group) -> str:
    """返回当前的回应者角色"""
    return C.ROLE_P2 if g.proposer == C.ROLE_P1 else C.ROLE_P1


def compute_payoffs_if_end(g: Group):
    """结算到 group 字段 + 玩家 payoff（本轮）"""
    # 计算原始点数
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

    # 计算折扣率
    discount_p1 = get_discount_rate(g.stage, C.ROLE_P1)
    discount_p2 = get_discount_rate(g.stage, C.ROLE_P2)

    # 应用折扣
    g.p1_discounted_points = g.p1_points * discount_p1
    g.p2_discounted_points = g.p2_points * discount_p2

    # T1 treatment: 两个人类玩家
    players = g.get_players()
    p1 = g.get_player_by_id(1)
    p2 = g.get_player_by_id(2)

    # 根据玩家的角色分配 payoff
    if p1.role() == C.ROLE_P1:
        p1.payoff = cu(g.p1_discounted_points)
        p2.payoff = cu(g.p2_discounted_points)
    else:
        p1.payoff = cu(g.p2_discounted_points)
        p2.payoff = cu(g.p1_discounted_points)

    print(f"[compute_payoffs] T1 treatment - P1 payoff={p1.payoff}, P2 payoff={p2.payoff}")


# ----------------- pages -----------------
class Start(Page):
    @staticmethod
    def is_displayed(p: Player):
        # 只在第一轮显示
        return p.round_number == 1


# ==================== Stage 1 页面 ====================

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
            t=p.treatment,
            my_discount=my_discount,
            opponent_type="対戦相手"
        )

    @staticmethod
    def error_message(p: Player, values):
        """验证表单输入"""
        if values['offer_points'] is None:
            return '手渡すポイントを入力してください / Please enter an offer'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        g: Group = p.group

        offer = p.field_maybe_none('offer_points')

        if timeout_happened or offer is None:
            g.offer_points = 0
            print(f"[Bargain_Propose] Player {p.participant.id_in_session} "
                  f"TIMEOUT or NO INPUT - default offer = 0")
        else:
            g.offer_points = offer
            print(f"[Bargain_Propose] Player {p.participant.id_in_session} "
                  f"offers {offer} points")

            #  根据当前stage保存offer到对应字段
        if g.stage == 1:
            p.stage_1_offer = offer
        elif g.stage == 2:
            p.stage_2_offer = offer
        elif g.stage == 3:
            p.stage_3_offer = offer

        g.offer_locked = True
        p.accepted_offer = None
        print(f"[Bargain_Propose] Offer locked at Stage {g.stage}")


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
        my_discounted_offer = round(float(g.offer_points) * my_discount, 2)


        return dict(
            stage=g.stage,
            offer=g.offer_points,
            my_discounted_offer=round(my_discounted_offer, 2),
            you=p.assigned_role,
            other=g.proposer,
            endowment=C.ENDOWMENT,
            t=p.treatment,
            my_discount=my_discount,
            opponent_type="対戦相手"
        )

    @staticmethod
    def error_message(p: Player, values):
        """验证表单输入"""
        if 'accepted_offer' not in values or values['accepted_offer'] is None:
            return '受け入れるか拒否するかを選択してください / Please select Accept or Reject'

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        g: Group = p.group

        accepted_value = p.field_maybe_none('accepted_offer')

        if timeout_happened:
            decision = False
            print(f"[Bargain_Respond] Player {p.participant.id_in_session} TIMEOUT - default to REJECT")
        elif accepted_value is None:
            decision = False
            print(f"[Bargain_Respond] Player {p.participant.id_in_session} NO CHOICE - default to REJECT")
        else:
            decision = accepted_value
            print(f"[Bargain_Respond] Player {p.participant.id_in_session} "
                  f"{'ACCEPTS' if decision else 'REJECTS'}")

            #  根据当前stage保存回应到对应字段
            if g.stage == 1:
                p.stage_1_accepted = decision
            elif g.stage == 2:
                p.stage_2_accepted = decision
            elif g.stage == 3:
                p.stage_3_accepted = decision

        if decision:
            g.accepted = True
            g.finished = True
            g.offer_locked = False
            compute_payoffs_if_end(g)
            print(f"[Bargain_Respond] ✅ Accepted at Stage {g.stage}")
        else:
            g.accepted = False
            old_stage = g.stage

            g.stage += 1

            if g.stage > C.MAX_STAGE:
                g.finished = True
                g.offer_locked = False
                compute_payoffs_if_end(g)
                print(f"[Bargain_Respond] ❌ Max stage reached")
            else:
                g.proposer = respondent_role(g)
                g.offer_locked = False
                g.offer_points = 0

                # 🔴 清空所有玩家的表单字段，避免粘连
                for player in g.get_players():
                    player.offer_points = None
                    player.accepted_offer = None  # 清空回应者的选择
                print(f"[Bargain_Respond] ❌ Rejected, Stage {old_stage}→{g.stage}")
                print(f"[Bargain_Respond] 🔄 Cleared all players' form fields for new stage")

class WaitAfterResponse(WaitPage):
    title_text = "お待ちください"
    body_text = "相手の応答を待ってください..."

    @staticmethod
    def is_displayed(p: Player):
        g: Group = p.group
        return (not g.finished) and g.offer_locked


# ==================== Stage 2 页面 ====================

class Bargain_Propose_Stage2(Page):
    form_model = 'player'
    form_fields = ['offer_points']
    template_name = 'human_human/Bargain_Propose.html'

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
        """验证表单输入"""
        if values['offer_points'] is None:
            return '手渡すポイントを入力してください / Please enter an offer amount'

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
    template_name = 'human_human/Bargain_Respond.html'

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
        """验证表单输入"""
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


# ==================== Stage 3 页面 ====================

class Bargain_Propose_Stage3(Page):
    form_model = 'player'
    form_fields = ['offer_points']
    template_name = 'human_human/Bargain_Propose.html'

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
        """验证表单输入"""
        if values['offer_points'] is None:
            return '手渡すポイントを入力してください / Please enter an offer amount'

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
    template_name = 'human_human/Bargain_Respond.html'

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
        """验证表单输入"""
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


# ==================== 结果页面 ====================

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

        # 获取玩家的折扣后点数
        if p.assigned_role == C.ROLE_P1:
            my_discounted_points = g.p1_discounted_points
            my_original_points = g.p1_points
        else:
            my_discounted_points = g.p2_discounted_points
            my_original_points = g.p2_points

        # 判断玩家是否是提议者
        is_proposer = (p.assigned_role == g.proposer)

        # 计算玩家获得的原始点数（用于显示）
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
            opponent_type="人類プレイヤー",
            t=p.treatment,
            current_round=p.round_number
        )

    @staticmethod
    def before_next_page(p: Player, timeout_happened):
        """保存每轮数据到 participant.vars"""
        # 初始化字典（如果不存在）
        if 'all_rounds_payoffs' not in p.participant.vars:
            p.participant.vars['all_rounds_payoffs'] = {}

        g: Group = p.group

        # 获取该玩家的点数
        if p.assigned_role == C.ROLE_P1:
            my_points = g.p1_discounted_points
        else:
            my_points = g.p2_discounted_points

        # 保存到 participant.vars
        p.participant.vars['all_rounds_payoffs'][p.round_number] = {
            'points': my_points,
            'role': p.assigned_role,
            'stage': g.stage,
            'accepted': g.accepted,
            'app_name': 'human_human'
        }


class WaitForNextRound(WaitPage):
    """等待所有玩家完成当前轮次"""

    title_text = "お待ちください"
    body_text = "他の参加者がこのラウンドを終了するのを待ってください..."

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(p: Player):
        # 在非最后一轮显示
        return p.round_number < C.NUM_ROUNDS

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        """所有玩家到达后的处理"""
        print(f"[WaitForNextRound] All players completed round {subsession.round_number}")
        print(f"[WaitForNextRound] Proceeding to round {subsession.round_number + 1}...")


class WaitForFinalResults(WaitPage):
    """等待所有玩家完成所有轮次后再显示最终结果"""

    title_text = "お待ちください"
    body_text = "全ての参加者が実験を終了するのを待ってください..."
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(p: Player):
        # 只在最后一轮显示
        return p.round_number == C.NUM_ROUNDS

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        """所有玩家到达后的处理（可选）"""
        print(f"[WaitForFinalResults] All players completed round {subsession.round_number}")
        print(f"[WaitForFinalResults] Proceeding to final results...")



# ==================== 页面序列 ====================

page_sequence = [
    Start,
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
    WaitForNextRound,
    WaitForFinalResults,
]
