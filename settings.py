
SESSION_CONFIGS = [
    dict(
        name='human_human_demo',
        display_name='human human Demo',
        app_sequence=['instruction','quiz','human_human_Practice','human_human','questionnaireT1', 'FinalResults'],
        num_demo_participants=2,
        treatment='T1',  # 👈 添加 treatment 参数
    ),
    dict(
        name='human_AI_bargaining1_demo',
        display_name='human AI Bargaining1 Demo',
        app_sequence=['instruction','quiz','human_AI_bargaining_Practice','human_AI_bargaining1', 'questionnaireT3','FinalResults'],
        num_demo_participants=3,
        treatment='T2',  # 👈 添加 treatment 参数 jdhjskhdj
    ),
    dict(
        name='human_AI_bargaining2_demo',
        display_name='human AI Bargaining2 Demo',
        app_sequence=['instruction','quiz','human_AI_bargaining_Practice','human_AI_bargaining2', 'questionnaireT3','FinalResults'],
        num_demo_participants=2,
        treatment='T3',  # 👈 添加 treatment 参数
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.0,
    participation_fee=0.0,
    doc="",
)


import os

SECRET_KEY = os.environ.get('OTREE_SECRET_KEY', 'dev-secret-change-me')

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get('OTREE_ADMIN_PASSWORD', 'otree')


PARTICIPANT_FIELDS = [
    'treatment',
    'final_bonus_yen',
    'final_source',
    'pay_round',
    'my_role_in_pay_round',
    'final_payoff',
    'final_round',
    'use_ai_payoff',
    'payment_source',
    'payment_source_player_id',
    'ai_role_in_that_game',
    'used_fallback',
    'original_pay_round'
]
SESSION_FIELDS = []

LANGUAGE_CODE = 'ja'

# 👇 移除或注释掉这一行，让 treatment 由 session 决定
# Treatment = 'T3'

REAL_WORLD_CURRENCY_CODE = 'JPY'
USE_POINTS = True

# rooms
ROOMS = [
    dict(
        name='pclab',
        display_name='社研PCラボ',
        participant_label_file='_rooms/pclab.txt',
    ),
    dict(name='live_demo', display_name='Room for live demo (no participant labels)'),
    dict(
        name='virtual_Lab',
        display_name='Room for virtual Lab 40 subjects (sub**)',
        participant_label_file='_rooms/virtualLab.txt',
    )
]

DEBUG = False

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

DEMO_PAGE_INTRO_HTML = """
<p>Click the config to create a demo session.</p>
"""

INSTALLED_APPS = ['otree']

SECRET_KEY = 'dev-secret-key'


