from otree.api import *
from ._lexicon_q import Lexicon

doc = """
questionnaireT1
"""

class C(BaseConstants):
    NAME_IN_URL = 'questionnaireT1'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    age = models.IntegerField(
        min=17, max=100,
        label = Lexicon.q_age
    )
    gender = models.IntegerField(
        label = Lexicon.q_gender,
        choices = Lexicon.q_gender_opts
    )
    affiliate = models.IntegerField(
        label = Lexicon.q_affiliate,
        choices = Lexicon.q_affiliate_opts
    )
    rule = models.IntegerField(
        label = Lexicon.q_rule,
        choices = Lexicon.q_rule_opts
    )
    offer_1 = models.IntegerField(
        label=Lexicon.q_offer_1,
        choices=Lexicon.q_offer_1_opts
    )
    offer_2= models.IntegerField(
        label = Lexicon.q_offer_2,
        choices = Lexicon.q_offer_2_opts
    )
    offer_3 = models.IntegerField(
        label=Lexicon.q_offer_3,
        choices=Lexicon.q_offer_3_opts
    )
    offer_4 = models.IntegerField(
        label=Lexicon.q_offer_4,
        choices=Lexicon.q_offer_4_opts
    )
# PAGES

class Start(Page):
    pass

def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'label',  'id_in_group',
    'age','gender',
    'affiliate','rule','offer_1','offer_2','offer_3','offer_4']
    for p in players:
        participant = p.participant
        session = p.session
        yield [
        session.code, participant.code, participant.label,  p.id_in_group, 
        p.age, p.gender,
        p.affiliate, p.rule, p.offer_1,p.offer_2
        ]      


class Questions(Page):
    form_model = 'player'
    form_fields = ['age', 'gender',
                    'affiliate','rule','offer_1',
                    'offer_2','offer_3','offer_4']
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            Lexicon=Lexicon,
        )

class Qfinish(Page):
    pass

page_sequence = [Questions,Qfinish]
