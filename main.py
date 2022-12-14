
STATE_REQUEST_KEY = 'session'
STATE_RESPONSE_KEY = 'session_state'
STATE_UPDATE_REQUEST_KEY = 'user'
STATE_UPDATE_RESPONSE_KEY = 'user_state_update'


file = open('questions.txt', 'r', encoding='UTF-8')
questions = [line.strip(';').split(';') for line in file]


def get_question(number, questions):
    question = questions[number - 1]

    if question[2] == 'main':
        text = question[3] + '\n' + question[4]
        start = 5
    else:
        text = question[2]
        start = 3
    answers = {}
    cnt = 1
    for el in range(start, len(question), 2):
        answers[cnt] = {
            'text': question[el],
            'points': int(question[el + 1])
        }
        cnt += 1

    question = {
        'module': question[1],
        'text': text,
        'answers': answers,
    }

    return question


def make_response(text='', tts=None, card=None, state=None, state_update=None, buttons=None, end_session=False):
    response = {
        'text': text,
        'tts': tts if tts is not None else text,
        'end_session': end_session,
    }

    if card is not None:
        response['card'] = card

    if buttons:
        response['buttons'] = buttons

    webhook_response = {
        'response': response,
        'version': '1.0',
    }

    if state is not None:
        webhook_response[STATE_RESPONSE_KEY] = state

    if state_update is not None:
        webhook_response[STATE_UPDATE_RESPONSE_KEY] = state_update
    else:
       webhook_response[STATE_UPDATE_RESPONSE_KEY] = None 

    return webhook_response


def card_big_image(image_id: str, title, description,) -> tuple:
    card = {
        "type": "BigImage",
        "image_id": image_id,
        "title": title,
        "description": description,
        # "button": {
        #    "text": "Надпись на кнопке",
        #    "url": "http://example.com/",
        #    "payload": {}
        # }
    }
    return card


def button(title, payload=None, url=None, hide=False,):
    button = {
        'title': title,
        'hide': hide,
    }

    if payload is not None:
        button['payload'] = payload

    if url is not None:
        button['url'] = url

    return button


def welcome_message(event, state):
    text = 'Привет, я помогу определить твой уровень в UI/UX дизайне. Для этого нужно пройти тест. У тебя есть в запасе 10 минут?'
    button_list = [
        button('Да', hide=True,),
        button('Нет', hide=True,),
        button('Помощь', hide=True),
    ]
    return make_response(text, buttons=button_list, state=state)


def prestart_test_ui_ux(event):
    '''Обработчик события Начать тест'''
    state = event['state'][STATE_REQUEST_KEY]
    text = 'Отлично! Я буду задавать тебе вопросы по разным навыкам, а ты выбирай варианты ответа, которые соответствуют твоему уровню. Например, “Алиса, Вариант 1”. Хорошо?'
    button_list = [
        button('Нет', hide=True,),
        button(
            'Да',
            hide=True,
        )
    ]

    state['screen'] = 'prestart_test_ui_ux'
    return make_response(text, buttons=button_list, state=state)


def test_in_process(event):
    #global questions
    state = event.get('state', {}).get(STATE_REQUEST_KEY)
    state['current_block'] = state['question']['module']
    state['screen'] = 'question'
    user_points = 'Набрано баллов: {}\n'.format(state['user_points'])
    # text = 'Сперва определим твой уровень владения Фигмой. Вопрос № {}'.format(
    #    state['question_number'])
    user_points = ''

    question = state['question']
    text = user_points + question['text'] + '\n'

    button_list = []

    for num, answer in question['answers'].items():
        button_list.append(
            button(
                'Вариант № {}'.format(num),
                hide=True,
            )
        )
        text += str(num) + '. ' + answer['text'] + '\n'
    #
    return make_response(text, state=state, buttons=button_list)


def repeat_question(event):

    response = test_in_process(event)

    response['response']['text'] = 'Повторяю вопрос\n' + \
        response['response']['text']

    return response


def end_test(event):
    text = 'Отлично, ты закончил тест! Ты набрал {} баллов'.format(
        event['state'][STATE_REQUEST_KEY]['user_points'])

    return make_response(text, state=event['state'][STATE_REQUEST_KEY])


def fallback(event):
    text = 'Сожалею, что у меня не получилось. Уже работаю над тем, чтобы исправиться. Если захочешь вернуться, я буду ждать тебя здесь.'

    return make_response(text, state=event['state'][STATE_REQUEST_KEY])


def are_you_sure(event):
    state = event['state'][STATE_REQUEST_KEY]
    text = 'Супер! Тебе предстоит ответить на 34 вопроса, касающихся разных навыков. В конце теста ты узнаешь свой уровень и получишь персональные рекомендации по улучшению отстающих навыков. Если тебе надоест, скажи “Алиса, хватит”. Ты всегда сможешь продолжить с того момента, на котором остановился. Приступаем?'

    button_list = [
        button('Нет',
               hide=True,
               ),
        button('Да',
               hide=True,
               )
    ]
    state['screen'] = 'are_you_sure'
    return make_response(text, buttons=button_list, state=state)


def user_help(event):
    text = 'Я предлагаю тебе пройти тест и определить твой уровень в UX/UI дизайне. Ответь “Да” или “Нет”. У тебя есть в запасе 10 минут?'

    button_list = [
        button('Нет',
               hide=True,
               ),
        button('Да',
               hide=True,
               )
    ]
    return make_response(text, buttons=button_list, state=event['state'][STATE_REQUEST_KEY])


def close(event):
    text = 'Очень жаль. Возвращайся, когда будешь готов.'

    return make_response(text, end_session=True)


def repeat_answer(event):
    state = event['state'][STATE_REQUEST_KEY]
    intents = event['request'].get('nlu', {}).get('intents')
    question = state['question']
    number = intents['repeat_answer']['slots']['number']['value'][4:]
    text = 'Повторяю вариант ответа № {}:\n{}'.format(
        number, state['question']['answers'][number]['text'])
    return make_response(text, state=state)


def is_not_new_session(event):
    state = event['state'][STATE_REQUEST_KEY]
    intents = event['request'].get('nlu', {}).get('intents')
    number = intents['repeat_answer']['slots']['number']['value'][4:]
    text = 'Это не новая сессия. Номер вопроса, на котором ты остановился {number}'
    return make_response(text, state=event['state'][STATE_REQUEST_KEY])


def handler_2(event, context):
    state = event['state'].get(STATE_REQUEST_KEY, {})
    state_update = event['state'].get(STATE_UPDATE_REQUEST_KEY, {})
    intents = event['request'].get('nlu', {}).get('intents')
    if 'reset' in intents:
        for key, value in state_update.items():
            state_update[key] = None

        return make_response(text='Сбросили все, что можно', state_update=state_update)

    if event['session']['new']:
        if state_update:

            return make_response(text='Вот, что мы сохранили в последний раз {}'.format(str(state_update)[:100]))
        user_state = {
            'my_value': 0,
            'screen': 'home'
        }

        return make_response(text='Это новая сессия', state=user_state)

    state['my_value'] += 1

    text = str(state)[100:] + '|||' + str(state_update)[100:]

    if 'exit' in intents:
        return make_response(text='Закончили сессию {}'.format(text), state=state, state_update=state, end_session=True)

    return make_response(text='Это уже не новая сессия {}'.format(text), state=state)


def handler(event, context):
    global questions
    state_update = event.get('state', {}).get(STATE_UPDATE_RESPONSE_KEY)

    if event['session']['new']:
        user_state = {
            'test_process': 'not started',  # Может быть 3 состояния not started, process, ended
            'question_number': 0,
            # 8 вариантов - None, figma, ui_skills, ux_skills, analytics, system_thinking, personal_skills, team_skills
            'current_block': None,
            'user_points': {
                'figma': 0,
                'ui_skills': 0,
                'ux_skills': 0,
                'analytics': 0,
                'system_thinking': 0,
                'personal_skills': 0,
                'team_skills': 0,
            },
            'screen': 'welcome_message',
        }

        return welcome_message(event, state=user_state)

    state = event['state'][STATE_REQUEST_KEY]

    intents = event['request'].get('nlu', {}).get('intents')
    action = event['request'].get('payload', {}).get('action')

    if state['screen'] == 'welcome_message':
        if 'YANDEX.CONFIRM' in intents:
            return prestart_test_ui_ux(event)
        elif 'YANDEX.REJECT' in intents:
            return close(event)
        elif 'YANDEX.HELP' in intents:
            return user_help(event)
        else:
            return fallback(event)
    elif state['screen'] == 'prestart_test_ui_ux':
        if 'YANDEX.CONFIRM' in intents:
            return are_you_sure(event)
        elif 'YANDEX.REJECT' in intents:
            return fallback(event)
        else:
            return fallback(event)
    elif state['screen'] == 'are_you_sure':
        if 'YANDEX.CONFIRM' in intents:
            state['question_number'] = 1
            state['test_process'] = 'process'
            state['question'] = get_question(
                state['question_number'], questions)
            return test_in_process(event)
        elif 'YANDEX.REJECT' in intents:
            return close(event)
        else:
            return fallback(event)
    elif state['screen'] == 'question':
        if 'user_answer' in intents:
            state['question_number'] += 1
            number = intents['user_answer']['slots']['number']['value'][4:]
            state['user_points'][state['current_block']
                                 ] += state['question']['answers'][number]['points']

            if state['question_number'] <= len(questions):
                state['question'] = get_question(
                    state['question_number'], questions)
            else:
                state['test_process'] = 'ended'
                return end_test(event)

            return test_in_process(event)
        elif 'repeat_question' in intents or "YANDEX.REPEAT" in intents:
            return repeat_question(event)
        elif 'repeat_answer' in intents:
            return repeat_answer(event)
        else:
            return fallback(event)

    elif 'help_user' in intents or 'YANDEX.HELP' in intents:
        return user_help(event)
    elif ('repeat_question' in intents or "YANDEX.REPEAT" in intents) and state['question_number'] > 0:
        return repeat_question(event)
    else:
        return fallback(event)
