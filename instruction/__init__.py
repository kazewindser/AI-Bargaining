from otree.api import *

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'instruction'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES
class Waitplease(Page):
    pass


class Instruction(Page):
    @staticmethod
    def vars_for_template(player: Player):
        session = player.session

        # 根据 session 的 config_name 来判断 treatment
        if 'human_human' in session.config['name']:
            treatment = 'T1'
            slide_path = 'instruction/T1.html'
        elif 'human_AI_bargaining1' in session.config['name']:
            treatment = 'T2'
            slide_path = 'instruction/T2.html'
        elif 'human_AI_bargaining2' in session.config['name']:
            treatment = 'T3'
            slide_path = 'instruction/T3.html'
        else:
            # 默认值
            treatment = 'T1'
            slide_path = 'instruction/T1.html'

        # 保存 treatment 到 participant
        player.participant.treatment = treatment

        return dict(
            slide_path=slide_path,
            treatment=treatment
        )


page_sequence = [Waitplease, Instruction]