from otree.api import *

doc = """
実験クイズアプリ - 6問の理解度確認テスト
"""


class C(BaseConstants):
    NAME_IN_URL = 'quiz'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 6

    QUESTIONS = [
        {
            'question': '本実験では、合計で何ラウンド実施されますか？',
            'choices': [
                [1, '1'],
                [2, '4'],
                [3, '8'],
                [4, '10']
            ],
            'correct': 4,
            'error_msg': '残念ですが、不正解です。'
        },
        {
            'question': '1ラウンドは最大で第何ステージまで行われますか？',
            'choices': [
                [1, '1'],
                [2, '2'],
                [3, '3'],
                [4, '4']
            ],
            'correct': 3,
            'error_msg': '残念ですが、不正解です。'
        },
        {
            'question': 'あなたがP2のとき、ステージ2では、あなたがP1にオファーを出しますか？',
            'choices': [
                [1, 'はい'],
                [2, 'いいえ']
            ],
            'correct': 1,
            'error_msg': '残念ですが、不正解です。P2はステージ2でP1にオファーを出します。ステージ1とステージ3では、P1からのオファーを受け入れるかどうかを決定します。'
        },
        {
            'question': 'あなたがP1のとき、ステージ2でP2があなたに50ポイントを提案しました。提案を受け入れた場合、割引後にあなたが最終的に得るポイントはいくつですか？',
            'choices': [
                [1, '0'],
                [2, '10'],
                [3, '20'],
                [4, '30']
            ],
            'correct': 4,
            'error_msg': '残念ですが、不正解です。P1のステージ2における割引率は0.6です。'
        },
        {
            'question': 'あなたがP2のとき、ステージ3でP1があなたに50ポイントを提案しました。提案を受け入れた場合、割引後にあなたが最終的に得るポイントはいくつですか？',
            'choices': [
                [1, '0'],
                [2, '8'],
                [3, '15'],
                [4, '50']
            ],
            'correct': 2,
            'error_msg': '残念ですが、不正解です。P2のステージ3における割引率は0.16です。'
        },
        {
            'question': 'あなたがP2のとき、ステージ3でP1があなたに50ポイントを提案しました。提案を拒否した場合、割引後にあなたが最終的に得るポイントはいくつですか？',
            'choices': [
                [1, '0'],
                [2, '8'],
                [3, '20'],
                [4, '50']
            ],
            'correct': 1,
            'error_msg': '残念ですが、不正解です。ステージ3でオファーが拒否された場合、P1とP2の得点はどちらも0になります。その時点でゲームは自動的に終了します。'
        }
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    answer = models.IntegerField()


class Start(Page):
    @staticmethod
    def is_displayed(p: Player):
        # 只在最后一轮显示
        return p.round_number == 1


class QuestionPage(Page):
    form_model = 'player'
    form_fields = ['answer']

    @staticmethod
    def vars_for_template(player: Player):
        question_data = C.QUESTIONS[player.round_number - 1]
        return {
            'question_num': player.round_number,
            'question_text': question_data['question'],
            'choices': question_data['choices'],
        }

    @staticmethod
    def error_message(player: Player, values):
        question_data = C.QUESTIONS[player.round_number - 1]
        if values['answer'] != question_data['correct']:
            return question_data['error_msg']


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

class WaitForPlayers(WaitPage):
    """等待所有玩家完成所有轮次后再显示最终结果"""

    title_text = "お待ちください"
    body_text = "全ての参加者がクイズを終了するのを待ってください..."
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(p: Player):
        # 只在最后一轮显示
        return p.round_number == C.NUM_ROUNDS

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        pass


page_sequence = [Start,QuestionPage, Results, WaitForPlayers]