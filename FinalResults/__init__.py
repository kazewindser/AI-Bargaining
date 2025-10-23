from otree.api import *
import random

doc = """
最终支付结算页面
根据不同的app(原T1/T2/T3)计算最终支付
"""


class C(BaseConstants):
    NAME_IN_URL = 'FinalResults'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    # 支付倍数
    MULTIPLIER = 30
    BASE_BONUS = 500
    # 角色定义
    ROLE_P1 = 'P1'
    ROLE_P2 = 'P2'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    """Player model for FinalResults"""
    # 存储计算结果
    selected_round = models.IntegerField(initial=0, doc="被抽中的轮次")
    selected_round_points = models.FloatField(initial=0, doc="被抽中轮次的点数")
    final_payment = models.FloatField(initial=0, doc="最终支付金额(日元)")
    payment_source = models.StringField(initial='', doc="支付来源:own/ai/fallback")
    used_ai_payoff = models.BooleanField(initial=False, doc="是否使用了AI收益")
    my_role_in_selected_round = models.StringField(initial='', doc="在被抽中轮次的角色")

    # 🔴 新增:用于存储AI的participant ID(如果使用了AI收益)
    ai_participant_id = models.IntegerField(initial=0, doc="AI玩家的participant ID")
    # 🔴 新增:用于存储原始抽选的玩家自己的轮次
    original_selected_round = models.IntegerField(initial=0, doc="原始抽选的玩家自己的轮次")
    # 🔴 新增:用于存储AI被选中的轮次
    ai_selected_round = models.IntegerField(initial=0, doc="AI被选中的轮次")


# FUNCTIONS
def creating_session(subsession: Subsession):
    """初始化session"""
    pass


# PAGES
class FinalResultsPage(Page):
    """最终结果页面"""

    template_name = 'FinalResults/FinalResults.html'

    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def vars_for_template(player: Player):
        """准备模板变量 - 在页面加载时就执行计算"""
        participant = player.participant
        session = player.session

        # 如果还没有计算支付,现在计算
        if player.selected_round == 0:
            print(f"[FinalResultsPage] Starting payment calculation for Player {participant.id_in_session}")

            # 🔴 修改：找到正确的游戏 app（跳过 quiz 和 practice）
            app_sequence = session.config['app_sequence']
            previous_app = None
            for app in app_sequence:
                if app in ['human_human', 'human_AI_bargaining1', 'human_AI_bargaining2']:
                    previous_app = app
                    break

            if previous_app is None:
                print(f"[FinalResultsPage] ERROR: Could not identify game app from {app_sequence}")
                previous_app = 'human_human'  # 默认值

            # 从所有回合中随机抽取
            pay_round = random.randint(1, 10)
            player.selected_round = pay_round

            print(f"[FinalResultsPage] Selected round {pay_round} for previous_app: {previous_app}")

            # 根据不同的app执行不同的逻辑
            if previous_app == 'human_human':
                calculate_human_human_payment(player, pay_round)
            elif previous_app == 'human_AI_bargaining1':
                calculate_human_ai1_payment(player, pay_round)
            elif previous_app == 'human_AI_bargaining2':
                calculate_human_ai2_payment(player, pay_round)

            # 保存到participant (🔴 移除 ai_participant_id)
            participant.pay_round = pay_round
            participant.final_payoff = player.selected_round_points
            participant.final_bonus_yen = player.final_payment
            participant.payment_source = player.payment_source
            participant.use_ai_payoff = player.used_ai_payoff
            participant.my_role_in_pay_round = player.my_role_in_selected_round

            print(f"[FinalResultsPage] Payment calculated - "
                  f"Round: {pay_round}, "
                  f"Role: {player.my_role_in_selected_round}, "
                  f"Points: {player.selected_round_points}, "
                  f"Payment: {player.final_payment} JPY, "
                  f"AI_ID: {player.ai_participant_id}, "
                  f"Original_Round: {player.original_selected_round}, "
                  f"AI_Round: {player.ai_selected_round}")
        else:
            print(
                f"[FinalResultsPage] Payment already calculated for Player {participant.id_in_session}, skipping recalculation")

        # 🔴 修改：使用相同的逻辑找到 previous_app
        app_sequence = session.config['app_sequence']
        previous_app = None
        for app in app_sequence:
            if app in ['human_human', 'human_AI_bargaining1', 'human_AI_bargaining2']:
                previous_app = app
                break

        app_display_names = {
            'human_human': 'Human vs Human (原T1)',
            'human_AI_bargaining1': 'Human vs AI Type 1 (原T2)',
            'human_AI_bargaining2': 'Human vs AI Type 2 (原T3)',
        }

        # 🔴 获取10轮的详细数据
        all_rounds_data = get_all_rounds_data(player, previous_app)

        return dict(
            treatment=app_display_names.get(previous_app, previous_app),
            pay_round=player.selected_round,
            my_points=round(player.selected_round_points, 2),
            multiplier=C.MULTIPLIER,
            base_bonus=C.BASE_BONUS,
            final_payment=round(player.final_payment, 2),
            payment_source=player.payment_source,
            used_ai_payoff=player.used_ai_payoff,
            my_role=player.my_role_in_selected_round,
            previous_app=previous_app or "",
            all_rounds_data=all_rounds_data,
            ai_participant_id=player.ai_participant_id,
            original_selected_round=player.original_selected_round,
            ai_selected_round=player.ai_selected_round
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        """确保数据已保存(此时计算已在 vars_for_template 中完成)"""
        participant = player.participant

        # 保存到participant (🔴 移除 ai_participant_id)
        participant.pay_round = player.selected_round
        participant.final_payoff = player.selected_round_points
        participant.final_bonus_yen = player.final_payment
        participant.payment_source = player.payment_source
        participant.use_ai_payoff = player.used_ai_payoff
        participant.my_role_in_pay_round = player.my_role_in_selected_round

        print(f"[FinalResultsPage] Data saved to participant for Player {participant.id_in_session}")


# ==================== 辅助函数 ====================

def get_all_rounds_data(player: Player, app_name: str) -> list:
    """
    获取所有10轮的数据用于展示

    Returns:
        list of dict: [{round: 1, role: 'P1', points: 50, stage: 2, accepted: True, participant_id: 1, is_ai: False}, ...]
    """
    participant = player.participant
    session = player.session

    all_data = []

    if app_name in ['human_human', 'human_AI_bargaining2']:
        # T1和T3:展示自己的10轮结果
        if 'all_rounds_payoffs' in participant.vars:
            for round_num in range(1, 11):
                round_data = participant.vars['all_rounds_payoffs'].get(round_num)
                if round_data:
                    all_data.append({
                        'round': round_num,
                        'role': round_data.get('role', ''),
                        'points': round(round_data.get('points', 0), 2),
                        'stage': round_data.get('stage', 0),
                        'accepted': round_data.get('accepted', False),
                        'participant_id': participant.id_in_session,
                        'is_ai': False  # 🔴 新增：标记这是玩家自己的数据
                    })

    elif app_name == 'human_AI_bargaining1':
        # T2:根据payment_source决定展示什么
        if player.payment_source == 'own' or player.payment_source == 'fallback':
            # 使用自己的结果:展示自己的10轮
            if 'all_rounds_payoffs' in participant.vars:
                for round_num in range(1, 11):
                    round_data = participant.vars['all_rounds_payoffs'].get(round_num)
                    if round_data:
                        all_data.append({
                            'round': round_num,
                            'role': round_data.get('role', ''),
                            'points': round(round_data.get('points', 0), 2),
                            'stage': round_data.get('stage', 0),
                            'accepted': round_data.get('accepted', False),
                            'participant_id': participant.id_in_session,
                            'is_ai': False  # 🔴 新增：标记这是玩家自己的数据
                        })

        elif player.payment_source == 'ai':
            # 🔴 修改：使用AI的结果时，既显示玩家自己的10轮，也显示所有同角色AI的结果
            my_role = player.my_role_in_selected_round

            # 1. 先添加玩家自己的10轮结果
            if 'all_rounds_payoffs' in participant.vars:
                for round_num in range(1, 11):
                    round_data = participant.vars['all_rounds_payoffs'].get(round_num)
                    if round_data:
                        all_data.append({
                            'round': round_num,
                            'role': round_data.get('role', ''),
                            'points': round(round_data.get('points', 0), 2),
                            'stage': round_data.get('stage', 0),
                            'accepted': round_data.get('accepted', False),
                            'participant_id': participant.id_in_session,
                            'is_ai': False
                        })

            # 2. 🔴 修改：添加所有同角色AI的结果
            for other_participant in session.get_participants():
                if other_participant.id_in_session == participant.id_in_session:
                    continue

                if 'all_rounds_payoffs' not in other_participant.vars:
                    continue

                # 检查这个participant的AI数据
                for round_num in range(1, 11):
                    round_data = other_participant.vars['all_rounds_payoffs'].get(round_num)
                    if round_data and round_data.get('app_name') == 'human_AI_bargaining1':
                        ai_role = round_data.get('ai_role', '')
                        # 🔴 如果AI的角色和当前玩家的角色相同
                        if ai_role == my_role:
                            ai_points = round_data.get('ai_points', 0)
                            all_data.append({
                                'round': round_num,
                                'role': ai_role,  # 🔴 AI的角色
                                'points': round(ai_points, 2),  # 🔴 AI的点数
                                'stage': round_data.get('stage', 0),
                                'accepted': round_data.get('accepted', False),
                                'participant_id': other_participant.id_in_session,
                                'is_ai': True  # 🔴 标记为AI数据
                            })

    return all_data


def calculate_human_human_payment(player: Player, round_num: int):
    """
    计算human_human(原T1)的支付
    逻辑:直接用自己在该轮的收益 × 20 + 500
    """
    try:
        participant = player.participant

        if 'all_rounds_payoffs' in participant.vars:
            round_data = participant.vars['all_rounds_payoffs'].get(round_num)

            if round_data:
                role = round_data.get('role', '')
                points = round_data.get('points', 0)

                player.my_role_in_selected_round = role
                player.selected_round_points = points
                player.payment_source = 'own'
                player.used_ai_payoff = False
                player.final_payment = points * C.MULTIPLIER + C.BASE_BONUS
                player.ai_participant_id = 0

                print(
                    f"[human_human] Player {participant.id_in_session}: Round {round_num}, Role {role}, Points {points}")
                return

        raise ValueError(f"No payoff data found in participant.vars for round {round_num}")

    except Exception as e:
        import traceback
        print(f"Error in calculate_human_human_payment: {e}")
        print(traceback.format_exc())
        player.selected_round_points = 0
        player.payment_source = 'error'
        player.final_payment = C.BASE_BONUS
        player.ai_participant_id = 0


def calculate_human_ai1_payment(player: Player, round_num: int):
    """
    计算human_AI_bargaining1(原T2)的支付
    🔴 修改后的逻辑:
    - 50%用自己的收益
    - 50%从**同一轮次**且**同角色**的AI玩家中随机抽取一个的收益
    """
    try:
        participant = player.participant

        if 'all_rounds_payoffs' not in participant.vars:
            raise ValueError("No payoff data found in participant.vars")

        round_data = participant.vars['all_rounds_payoffs'].get(round_num)

        if not round_data:
            raise ValueError(f"No payoff data found for round {round_num}")

        my_role = round_data.get('role', '')
        my_points = round_data.get('points', 0)

        player.my_role_in_selected_round = my_role
        player.original_selected_round = round_num  # 记录原始抽选的轮次

        print(f"[calculate_human_ai1_payment] Round={round_num}, Role={my_role}, My_points={my_points}")

        # 50/50概率
        use_ai = random.choice([True, False])
        player.used_ai_payoff = use_ai

        if use_ai:
            # 🔴 修改：从**同一轮次**且**同角色**的AI中随机抽取
            ai_result = get_random_ai_payoff_same_round(participant, round_num, my_role)

            if ai_result is not None:
                ai_points, ai_participant_id = ai_result
                player.selected_round_points = ai_points
                player.ai_selected_round = round_num  # 🔴 AI的轮次和玩家相同
                player.payment_source = 'ai'
                player.final_payment = ai_points * C.MULTIPLIER + C.BASE_BONUS
                player.ai_participant_id = ai_participant_id
                print(
                    f"[calculate_human_ai1_payment] Using AI payoff: {ai_points} from Participant {ai_participant_id}, Round {round_num}")
            else:
                # Fallback:用自己的
                player.selected_round_points = my_points
                player.payment_source = 'fallback'
                player.final_payment = my_points * C.MULTIPLIER + C.BASE_BONUS
                player.ai_participant_id = 0
                player.ai_selected_round = 0
                print(f"[calculate_human_ai1_payment] No matching AI found, using own: {my_points}")
        else:
            # 使用自己的收益
            player.selected_round_points = my_points
            player.payment_source = 'own'
            player.final_payment = my_points * C.MULTIPLIER + C.BASE_BONUS
            player.ai_participant_id = 0
            player.ai_selected_round = 0
            print(f"[calculate_human_ai1_payment] Using own payoff: {my_points}")

    except Exception as e:
        import traceback
        print(f"Error in calculate_human_ai1_payment: {e}")
        print(traceback.format_exc())
        player.selected_round_points = 0
        player.payment_source = 'error'
        player.final_payment = C.BASE_BONUS
        player.ai_participant_id = 0
        player.ai_selected_round = 0


def get_random_ai_payoff_same_round(my_participant, round_num: int, my_role: str):
    """
    🔴 新函数：从**同一轮次**且**同角色**的AI中随机抽取一个

    Args:
        my_participant: 当前玩家的participant
        round_num: 指定的轮次（必须相同）
        my_role: 玩家的角色（AI也必须是这个角色）

    Returns:
        tuple: (ai_points, participant_id) 或 None
    """
    try:
        session = my_participant.session

        # 收集所有符合条件的(participant, ai_points)组合
        all_options = []

        for other_participant in session.get_participants():
            # 跳过自己
            if other_participant.id_in_session == my_participant.id_in_session:
                continue

            # 检查是否有 payoff 数据
            if 'all_rounds_payoffs' not in other_participant.vars:
                continue

            # 🔴 关键：只查看指定的轮次
            round_data = other_participant.vars['all_rounds_payoffs'].get(round_num)

            if not round_data:
                continue

            # 检查是否是 human_AI_bargaining1 的数据
            if round_data.get('app_name') == 'human_AI_bargaining1':
                ai_role = round_data.get('ai_role', '')

                # 🔴 如果 AI 的角色和我的角色相同
                if ai_role == my_role:
                    # 使用 AI 的点数
                    ai_points = round_data.get('ai_points', 0)
                    all_options.append((ai_points, other_participant.id_in_session))

                    print(
                        f"[get_random_ai_payoff_same_round] Found option: Participant {other_participant.id_in_session}, "
                        f"Round {round_num}, AI_role={ai_role}, AI_points={ai_points}")

        if all_options:
            # 随机选择一个
            selected = random.choice(all_options)
            print(
                f"[get_random_ai_payoff_same_round] Found {len(all_options)} options for Round {round_num}, Role {my_role}, "
                f"selected: Participant {selected[1]}, AI_Points {selected[0]}")
            return selected

        print(f"[get_random_ai_payoff_same_round] No matching AI data found for Round {round_num}, Role {my_role}")
        return None

    except Exception as e:
        import traceback
        print(f"Error in get_random_ai_payoff_same_round: {e}")
        print(traceback.format_exc())
        return None


def get_all_rounds_data(player: Player, app_name: str) -> list:
    """
    获取所有10轮的数据用于展示

    Returns:
        list of dict: [{round: 1, role: 'P1', points: 50, stage: 2, accepted: True, participant_id: 1, is_ai: False}, ...]
    """
    participant = player.participant
    session = player.session

    all_data = []

    if app_name in ['human_human', 'human_AI_bargaining2']:
        # T1和T3:展示自己的10轮结果
        if 'all_rounds_payoffs' in participant.vars:
            for round_num in range(1, 11):
                round_data = participant.vars['all_rounds_payoffs'].get(round_num)
                if round_data:
                    all_data.append({
                        'round': round_num,
                        'role': round_data.get('role', ''),
                        'points': round(round_data.get('points', 0), 2),
                        'stage': round_data.get('stage', 0),
                        'accepted': round_data.get('accepted', False),
                        'participant_id': participant.id_in_session,
                        'is_ai': False
                    })

    elif app_name == 'human_AI_bargaining1':
        # T2:根据payment_source决定展示什么
        if player.payment_source == 'own' or player.payment_source == 'fallback':
            # 使用自己的结果:展示自己的10轮
            if 'all_rounds_payoffs' in participant.vars:
                for round_num in range(1, 11):
                    round_data = participant.vars['all_rounds_payoffs'].get(round_num)
                    if round_data:
                        all_data.append({
                            'round': round_num,
                            'role': round_data.get('role', ''),
                            'points': round(round_data.get('points', 0), 2),
                            'stage': round_data.get('stage', 0),
                            'accepted': round_data.get('accepted', False),
                            'participant_id': participant.id_in_session,
                            'is_ai': False
                        })

        elif player.payment_source == 'ai':
            # 🔴 修改：使用AI的结果时，只显示玩家自己的10轮 + 被选中的那一轮的同角色AI结果
            my_role = player.my_role_in_selected_round
            selected_round = player.original_selected_round  # 被抽中的轮次

            # 1. 先添加玩家自己的10轮结果
            if 'all_rounds_payoffs' in participant.vars:
                for round_num in range(1, 11):
                    round_data = participant.vars['all_rounds_payoffs'].get(round_num)
                    if round_data:
                        all_data.append({
                            'round': round_num,
                            'role': round_data.get('role', ''),
                            'points': round(round_data.get('points', 0), 2),
                            'stage': round_data.get('stage', 0),
                            'accepted': round_data.get('accepted', False),
                            'participant_id': participant.id_in_session,
                            'is_ai': False
                        })

            # 2. 🔴 修改：只添加**被抽中的轮次**中**同角色**的AI结果
            for other_participant in session.get_participants():
                if other_participant.id_in_session == participant.id_in_session:
                    continue

                if 'all_rounds_payoffs' not in other_participant.vars:
                    continue

                # 🔴 只检查被抽中的那一轮
                round_data = other_participant.vars['all_rounds_payoffs'].get(selected_round)

                if round_data and round_data.get('app_name') == 'human_AI_bargaining1':
                    ai_role = round_data.get('ai_role', '')

                    # 🔴 如果AI的角色和当前玩家的角色相同
                    if ai_role == my_role:
                        ai_points = round_data.get('ai_points', 0)
                        all_data.append({
                            'round': selected_round,  # 🔴 只有这一轮
                            'role': ai_role,
                            'points': round(ai_points, 2),
                            'stage': round_data.get('stage', 0),
                            'accepted': round_data.get('accepted', False),
                            'participant_id': other_participant.id_in_session,
                            'is_ai': True
                        })

    return all_data

def calculate_human_ai2_payment(player: Player, round_num: int):
    """
    计算human_AI_bargaining2(原T3)的支付
    逻辑:直接用自己在该轮的收益 × 20 + 500
    """
    try:
        participant = player.participant

        if 'all_rounds_payoffs' in participant.vars:
            round_data = participant.vars['all_rounds_payoffs'].get(round_num)

            if round_data:
                role = round_data.get('role', '')
                points = round_data.get('points', 0)

                player.my_role_in_selected_round = role
                player.selected_round_points = points
                player.payment_source = 'own'
                player.used_ai_payoff = False
                player.final_payment = points * C.MULTIPLIER + C.BASE_BONUS
                player.ai_participant_id = 0

                print(
                    f"[human_AI_bargaining2] Player {participant.id_in_session}: Round {round_num}, Role {role}, Points {points}")
                return

        raise ValueError(f"No payoff data found in participant.vars for round {round_num}")

    except Exception as e:
        import traceback
        print(f"Error in calculate_human_ai2_payment: {e}")
        print(traceback.format_exc())
        player.selected_round_points = 0
        player.payment_source = 'error'
        player.final_payment = C.BASE_BONUS
        player.ai_participant_id = 0


def get_random_ai_payoff(my_participant, my_role: str):
    """
    🔴 修复后的函数：从所有同角色AI中随机抽取一个(participant, round, points)组合
    
    注意：这里获取的是 AI 的点数，不是玩家的点数

    Returns:
        tuple: (ai_points, participant_id, round_num) 或 None
    """
    try:
        session = my_participant.session

        # 收集所有符合条件的(participant, round, ai_points)组合
        all_options = []

        for other_participant in session.get_participants():
            # 跳过自己
            if other_participant.id_in_session == my_participant.id_in_session:
                continue

            # 检查是否有 payoff 数据
            if 'all_rounds_payoffs' not in other_participant.vars:
                continue

            # 遍历所有轮次
            for round_num in range(1, 11):
                round_data = other_participant.vars['all_rounds_payoffs'].get(round_num)

                if not round_data:
                    continue

                # 🔴 关键修改：检查 AI 的角色是否和我的角色相同
                # 如果玩家是 P1，AI 是 P2，我们要找其他玩家对局中 AI 是 P1 的情况
                # 即：其他玩家是 P2，AI 是 P1
                if round_data.get('app_name') == 'human_AI_bargaining1':
                    ai_role = round_data.get('ai_role', '')
                    
                    # 如果 AI 的角色和我的角色相同
                    if ai_role == my_role:
                        # 🔴 使用 AI 的点数，不是玩家的点数
                        ai_points = round_data.get('ai_points', 0)
                        all_options.append((ai_points, other_participant.id_in_session, round_num))
                        
                        print(f"[get_random_ai_payoff] Found option: Participant {other_participant.id_in_session}, "
                              f"Round {round_num}, AI_role={ai_role}, AI_points={ai_points}")

        if all_options:
            # 随机选择一个
            selected = random.choice(all_options)
            print(
                f"[get_random_ai_payoff] Found {len(all_options)} options for role {my_role}, "
                f"selected: Participant {selected[1]}, Round {selected[2]}, AI_Points {selected[0]}")
            return selected

        print(f"[get_random_ai_payoff] No matching AI data found for role {my_role}")
        return None

    except Exception as e:
        import traceback
        print(f"Error in get_random_ai_payoff: {e}")
        print(traceback.format_exc())
        return None


page_sequence = [FinalResultsPage]