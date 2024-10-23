import time
import random
import streamlit as st
import snowflake.connector
from snowflake.connector import ProgrammingError
import pandas as pd
import uuid
from datetime import datetime, timedelta
import pytz


def generate_unique_id():
    return str(uuid.uuid4())  # Generates a random UUID


def exe_sf(conn, sql: str, return_as_df=True):
    cur = conn
    try:
        cursor = cur.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()

        # Convert data to DataFrame
        if return_as_df:
            columns = [col[0] for col in cursor.description]
            dataframe = pd.DataFrame(data, columns=columns)
            return dataframe
        else:
            return data

    finally:
        cur.close()

def create_conn():
    return snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            role=st.secrets["snowflake"]["role"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )

def get_queries(key:str, type:str = 'user'):
    return st.secrets['snowflake']['sql'][type][key]


class UserGUI:
    def __init__(self):
        self.miami_tz = pytz.timezone('America/New_York')
        self.list_correct_ans = [" Correct! You're moving on to the next question!",
                                        "That's absolutely right! You've earned your way to the next question!",
                                        "Correct! You're one step closer to the big prize – next question!"]


        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'add_code_page'

        if 'debug' not in st.session_state:
            st.session_state.debug = False

        if 'user_id_logged_in' not in st.session_state:
            st.session_state.user_id_logged_in = None
        elif (st.session_state.user_id_logged_in != None) & (st.session_state.current_page == 'add_code_page'):
            st.session_state.current_page = 'question_page'

        if 'index_questions_df' not in st.session_state:
            st.session_state.index_questions_df = 0
        if 'user_answer' not in st.session_state:
            st.session_state.user_answer = None
        if 'keep_playing' not in st.session_state:
            st.session_state.keep_playing = True
        if 'game_code' not in st.session_state:
            st.session_state.game_code = None
        if 'current_question_answers_list' not in st.session_state:
            st.session_state.current_question_answers_list = []
        # if "snowflake_connection" not in st.session_state:
        #     st.session_state.snowflake_connection = create_conn()
        if 'question_time_minutes' not in st.session_state:
            st.session_state.question_time_minutes = 3.0
        if 'datetime_question_target' not in st.session_state:
            st.session_state.datetime_question_target = None
        if 'playing_at' not in st.session_state:
            st.session_state.playing_at = datetime.now(self.miami_tz)

        if 'timer_display' not in st.session_state:
            st.session_state.timer_display = True
        if 'datetime_question_started' not in st.session_state:
            st.session_state.datetime_question_started = datetime.now(self.miami_tz)
        if 'datetime_question_current_time' not in st.session_state:
            st.session_state.datetime_question_current_time = None

        if 'answer_text' not in st.session_state:
            st.session_state.answer_text = ''
        if 'congrats_waiting_room' not in st.session_state:
            st.session_state.congrats_waiting_room = True

        if 'current_question_text' not in st.session_state:
            st.session_state.current_question_text = None
        if 'current_question_correct_answer' not in st.session_state:
            st.session_state.current_question_correct_answer = None

        if 'current_question_id' not in st.session_state:
            st.session_state.current_question_id = None
        if 'disable_question_buttons' not in st.session_state:
            st.session_state.disable_question_buttons = False

        if 'question_time_left' not in st.session_state:
            st.session_state.question_time_left = 15

        if 'show_wildcards' not in st.session_state:
            st.session_state.show_wildcards = False
        if 'wildcard_50_50_left' not in st.session_state:
            st.session_state.wildcard_50_50_left = 1
        if 'wildcard_audience_left' not in st.session_state:
            st.session_state.wildcard_audience_left = 1
        if 'wildcard_phone_left' not in st.session_state:
            st.session_state.wildcard_phone_left = 1

        if 'wildcard_50_50_act' not in st.session_state:
            st.session_state.wildcard_50_50_act = False
        if 'wildcard_audience_act' not in st.session_state:
            st.session_state.wildcard_audience_act = False
        if 'wildcard_phone_act' not in st.session_state:
            st.session_state.wildcard_phone_act = False

        if 'last_page' not in st.session_state:
            st.session_state.last_page = None

        if 'boolean_unique_answer_send' not in st.session_state:
            st.session_state.boolean_unique_answer_send = False
        if 'current_session_status' not in st.session_state:
            st.session_state.current_session_status = None
        if 'user_didnt_answer' not in st.session_state:
            st.session_state.user_didnt_answer = False

        self.t = 0  # Time default sleep
        if 'questions_df' not in st.session_state:
            st.session_state.questions_df = exe_sf(create_conn(),
                                  sql=get_queries('questions_df', type='df'))
        if 'score_df' not in st.session_state:
            st.session_state.score_df = exe_sf(create_conn(),
                              sql=get_queries('score_df_desc', type='df'))

        if 'multiple_choice_options_shuffle' not in st.session_state:
            num_list = [0, 1, 2, 3]
            random.shuffle(num_list)

            st.session_state.multiple_choice_options_shuffle = num_list  # First Time not Shuffle

        if 'get_datetime_question_started' not in st.session_state:
            st.session_state.get_datetime_question_started = False

        self.cmd_get_session_info = get_queries('session_info')

        self.cmd_get_users_answers_by_game_id = get_queries('users_answers_by_game_id')

        self.cmd_insert_game_answer = get_queries('insert_game_answer')

        self.cmd_update_user_question_id = get_queries('update_user_question_id')

        self.centered_buttons_questions = """
                                        <style>
                                        .stButton {
                                            display: flex;
                                            justify-content: center;
                                            font-weight: bold;
                                        }
                                        .answer-container {
                                            display: flex;
                                            justify-content: space-between;
                                            width: 100%;
                                        }
                                        .answer-text {
                                            flex-grow: 1; /* Ensure answer text takes up remaining space */
                                            text-align: center; /* Align answer text to the left */
                                            margin-left: 10px;
                                        }
                                        </style>
                                        """

    def reload_page(self):
        time.sleep(self.t)
        st.rerun()

    def next_page(self, name_page):
        # st.write(name_page)
        st.session_state.current_page = name_page
        self.reload_page()

    def add_code_page(self):
        st.header("JOIN TO GAME")
        st.session_state.game_code = st.text_input(
            "Insert Here Your Game Code!"
        )
        st.session_state.game_code = st.session_state.game_code.replace(" ", "").upper()

        if len(st.session_state.game_code) != 0 | st.button("JOIN"):
            try:
                # df = self.conn.query(self.cmd_get_session_info.format(st.session_state.game_code))
                # st.write(self.cmd_get_session_info.format(st.session_state.game_code))
                df = exe_sf(create_conn(), sql=self.cmd_get_session_info.format(st.session_state.game_code))
                # st.write(df)
                if len(df) == 0:
                    st.error("This is not a Valid Session Code 😢")
                elif len(df) == 1:
                    status = None
                    for row in df.itertuples():
                        status = row.SESSION_STATUS
                        st.session_state.game_code = row.SESSION_CODE

                    if status == "lobby":
                        st.success("This is a Valid Session Code")
                        time.sleep(3)

                        self.next_page("register_page")
                    elif status == 'finished':
                        st.error("This session game is over 🤷‍♂️")
                    else:
                        st.error("Sorry, this game already started 😶‍🌫️")
                else:
                    st.error("Unknown Error, we will fix soon... 🤥")
            except Exception as e:
                st.error(f"Error: {e}")

            st.session_state.last_page = 'add_code_page'

            # self.next_page("register_page")

    def get_other_option_selectbox(self, section, initial_options, other="Other"):
        initial_options.append(other)

        default_options = st.selectbox(
            section,
            initial_options
        )

        if default_options == other:
            new_option = st.text_input(f"Write here your {section}")
            st.session_state[f"user_{section.lower().replace(' ', '_')}"] = new_option
        else:
            st.session_state[f"user_{section.lower().replace(' ', '_')}"] = default_options

    def register_page(self):
        placeholder = st.empty()
        with placeholder.container():
            st.header("Register Here! 📃")
            # st.write(f"Now that you joined the game ({st.session_state.game_code}), you need to register:")

            register_values_free = ['First Name', 'Middle Name (Optional)', 'Last Name']
            register_values_options = {
                "Department": ["Actuarial", "Administration", "Claims", "Commercial", "Compliance", "Customer Service",
                               "Data Analytics", "Finance", "Human Resources", "Information Technology", "Legal",
                               "Marketing", "Medical Service", "Policy Administration", "Project Management", "Providers",
                               "Quality Control", "Risk", "Underwriting"],
                "Country": ["Ecuador", "Peru", "Colombia", "Venezuela", "Brazil", "Bolivia", "Chile", "Paraguay", "Uruguay",
                            "Argentina", "USA", "Canada", "Mexico"]
            }
            #self.next_page('question_page')

            for value in register_values_free:
                st.text_input(f"{value}", key=f"user_{value.lower().replace(' ', '_')}")

            for section, options in register_values_options.items():
                self.get_other_option_selectbox(section, options)

            if st.button("Lets Play! 🎮"):
                if st.session_state.user_first_name and st.session_state.user_last_name:
                    user_id = generate_unique_id()
                    SQL = get_queries('insert_user').format(user_id,
                           st.session_state.user_first_name,
                           st.session_state["user_middle_name_(optional)"],
                           st.session_state.user_last_name,
                           st.session_state.user_department,
                           st.session_state.user_country,
                           st.session_state.game_code
                           )
                    # st.write(SQL)
                    try:
                        # self.conn.query(SQL, ttl=600)
                        # self.conn.query("INSERT INTO PROD_DATASCIENCE_DB.PRJ_003_WHOWANTSTOBEAMILLIONAIRE.USERS_MAP (user_first_name, user_middle_name, user_last_name, user_department, user_country, group_game_session_id) VALUES ( 'Mateo', '', 'Sosa', 'Option2', 'Ecuador', 'WR514R' )", ttl=600)
                        exe_sf(create_conn(),
                               sql=SQL, return_as_df=False)
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
                    st.success("You Have Been Registered!")
                    st.session_state.user_id_logged_in = user_id
                    time.sleep(1.5)
                    self.next_page("question_page")
                else:
                    st.error("Please fill in all fields. The middle name is the only optional field!")

        st.session_state.last_page = 'register_page'

    def get_current_session_state(self):
        df = exe_sf(create_conn(), sql=self.cmd_get_session_info.format(st.session_state.game_code))
        try:
            return df["SESSION_STATUS"].iloc[0], int(df["SESSION_QUESTION_ID"].iloc[0]), df["PLAYING_AT"].iloc[0]
        except:
            return 'waiting', st.session_state.index_questions_df, datetime.now()

    def seconds_to_hms(self, seconds):
        minutes = (seconds % 3600) // 60  # Calculate remaining minutes
        seconds = seconds % 60  # Calculate remaining seconds
        return f"{minutes:02}:{seconds:02}"  # Format as HH:MM:SS

    def countdown_v2(self, datetime_question_started):
        seconds_to_spend = 60
        only_send_once = True
        # if st.session_state.question_time_left
        for i in range(seconds_to_spend):
            if not st.session_state.disable_question_buttons:
                datetime_question_current_time = datetime.now(self.miami_tz)
                st.session_state.question_time_left = (st.session_state.datetime_question_target - datetime_question_current_time ).total_seconds()
                # st.write(st.session_state.question_time_left)
                if (0 < st.session_state.question_time_left < 10) & (st.session_state.user_answer == None):
                    # if st.session_state.user_answer == None:
                    st.warning("Hurry up! You’ve only got a few seconds left! If you're unsure, just take a guess!")
                    time.sleep(1)
                    #     st.write('⏳ Please select an answer before the time runs out!⏳')
                    # else:
                    #     st.write("Time is almost up!")
                elif 0 < st.session_state.question_time_left:
                    minutes, seconds = divmod(st.session_state.question_time_left, 60)
                    st.subheader(f"⏳ {int(minutes):02d}:{int(seconds):02d} left")

                    time.sleep(1)
                else:
                    st.header('Time is over')
                    if only_send_once:
                        self.send_user_answer_by_question(datetime_question_started)
                        only_send_once = False

                        time.sleep(3)

    def countdown(self):
        timer_length = st.session_state.score_df.iloc[st.session_state.index_questions_df].QUESTION_TIME_MINUTES
        if st.session_state.question_time_left == None:
            st.session_state.question_time_left = int(timer_length * 60)

        # for seconds in range(st.session_state.question_time_left):
        for seconds in range(1):
            st.session_state.question_time_left -= 1
            if st.session_state.question_time_left < 30:
                st.warning("Hurry up! You’ve only got a few seconds left! If you're unsure, just take a guess!")
            st.write(f"⏳ {self.seconds_to_hms(st.session_state.question_time_left)} left")
            # time.sleep(1)

    def question_page(self):
        if st.session_state.get_datetime_question_started:
            st.session_state.current_session_status, st.session_state.index_questions_df, st.session_state.playing_at = self.get_current_session_state()

            st.session_state.congrats_waiting_room = True
            st.session_state.datetime_question_started = datetime.now(self.miami_tz)
            q_minutes = st.session_state.score_df.iloc[st.session_state.index_questions_df].QUESTION_TIME_MINUTES
            st.session_state.datetime_question_target = st.session_state.datetime_question_started + timedelta(minutes=q_minutes)
            st.session_state.get_datetime_question_started = False

            q = st.session_state.questions_df.iloc[st.session_state.index_questions_df]
            st.session_state.current_question_id = q["QUESTION_ID"]
            st.session_state.current_question_text = q["QUESTION"]
            st.session_state.current_question_answers_list = [q["CORRECT_ANSWER"], q["INCORRECT_OPTION_1"],
                                                              q["INCORRECT_OPTION_2"], q["INCORRECT_OPTION_3"]]
            st.session_state.current_question_correct_answer = q["CORRECT_ANSWER"]

            st.session_state.last_page = 'question_page'

        datetime_question_started = st.session_state.datetime_question_started.strftime('%Y-%m-%d %H:%M:%S')

        if (st.session_state.current_session_status == 'playing') & (st.session_state.keep_playing) & (st.session_state.last_page == 'question_page'):
            now = datetime.now(self.miami_tz)
            # st.write(now)
            # st.write(st.session_state.playing_at)
            # st.write(type(st.session_state.playing_at))

            localized_datetime = self.miami_tz.localize(st.session_state.playing_at)

            seconds_to_start = (localized_datetime - now).total_seconds()
            if seconds_to_start < 0:
                pass
            else:
                placeholder7 = st.empty()
                with placeholder7.container():
                    with st.spinner("Waiting for other players..."):
                        now = datetime.now(self.miami_tz)
                        seconds_to_start = (localized_datetime - now).total_seconds()

                        if seconds_to_start > 0:
                            time.sleep(seconds_to_start)

                placeholder7.empty()

            placeholder = st.empty()
            with placeholder.container():
            # with st.empty():
                if not st.session_state.disable_question_buttons:
                    st.markdown(self.centered_buttons_questions, unsafe_allow_html=True)
                    st.header("Question {}! ⁉️🤔".format(st.session_state.index_questions_df + 1))
                    st.subheader(st.session_state.current_question_text)  # Show Question

                    col1, col2 = st.columns(2)
                    with col1:
                        container_A = st.container(border=True)
                        container_C = st.container(border=True)
                    with col2:
                        container_B = st.container(border=True)
                        container_D = st.container(border=True)

                    answers = [st.session_state.current_question_answers_list[i] for i in st.session_state.multiple_choice_options_shuffle]
                    answer_containers = [container_A, container_B, container_C, container_D]

                    for i in range(len(answer_containers)):
                        index_char = chr(65 + i)  # 0 = A, 1 = B, ...

                        answer_containers[i].markdown(
                            f"""
                            <div class="answer-container">
                                <span class="answer-text">{answers[i]}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # answer_containers[i].write(answers[i])
                        if answer_containers[i].button(index_char, disabled=st.session_state.disable_question_buttons):
                            st.session_state.user_answer = answers[i]
                            st.session_state.answer_text = f"You've selected answer '{index_char}'"

                    if st.session_state.answer_text:
                        if st.button(f"{st.session_state.answer_text}. Is this your final Answer? (Double-click  to confirm your submission)",
                                     disabled=st.session_state.disable_question_buttons, type="primary"):
                            self.send_user_answer_by_question(datetime_question_started)
                        # st.warning()
                    else:
                        st.warning("Please select an option!")

                    if st.session_state.show_wildcards:
                        if (st.session_state.wildcard_50_50_left > 0) | (st.session_state.wildcard_50_50_act):
                            if st.button("50:50", icon="🔢") | (st.session_state.wildcard_50_50_act):
                                if not st.session_state.wildcard_50_50_act:
                                    st.session_state.wildcard_50_50_left -= 1
                                st.session_state.wildcard_50_50_act = True

                                a_to_eliminate = 2
                                for a in st.session_state.current_question_answers_list:
                                    if a == st.session_state.current_question_correct_answer:
                                        st.write("❔ {}".format(a))
                                    else:
                                        if a_to_eliminate > 0:
                                            st.write("❌ {}".format(a))
                                            a_to_eliminate -= 1
                                        else:
                                            st.write("❔ {}".format(a))

                        if (st.session_state.wildcard_phone_left > 0) | (st.session_state.wildcard_phone_act):
                            if (st.button("Phone a Friend", icon="📲")) | (st.session_state.wildcard_phone_act):
                                if not st.session_state.wildcard_phone_act:
                                    st.session_state.wildcard_phone_left -= 1
                                st.session_state.wildcard_phone_act = True

                                friend_answer, second_friend_ans = self.simulate_answer(95,
                                                                                        correct_A=st.session_state.current_question_answers_list[0],
                                                                                        incorrect_A=st.session_state.current_question_answers_list[1])

                                message = st.chat_message("Owl", avatar="🦉")
                                message.write("Hmmm... I’m almost sure about this. I’d say it’s: '{}'. But if I’m wrong, then maybe it’s: '{}'."
                                              .format(friend_answer, second_friend_ans))

                        if (st.session_state.wildcard_audience_left > 0) | (st.session_state.wildcard_audience_act):
                            if (st.button("Audience", icon="👥")) | (st.session_state.wildcard_audience_act):
                                if not st.session_state.wildcard_audience_act:
                                    st.session_state.wildcard_audience_left -= 1
                                st.session_state.wildcard_audience_act = True

                                # with st.empty():
                                #     # for seconds in range(st.session_state.question_time_left):
                                df_users_answers = exe_sf(create_conn(),
                                                          sql=self.cmd_get_users_answers_by_game_id.format(st.session_state.game_code,
                                                                                                           st.session_state.index_questions_df))

                                if len(df_users_answers) == 0:
                                    st.warning("Audience is answering")
                                else:
                                    grouped_agg = df_users_answers.groupby(['ANSWER']).agg({
                                        'ANSWER': ['count']
                                    })
                                    grouped_agg.columns = ['_'.join(col).strip() for col in grouped_agg.columns.values]
                                    grouped_agg.reset_index(inplace=True)

                                    # st.write(grouped_agg)
                                    st.bar_chart(grouped_agg, x="ANSWER", y="ANSWER_count", x_label="Answers",
                                                 y_label="Num Responded")
                                    # time.sleep(2)

                                if st.button("Update Audience Answers"):
                                    st.rerun()

                    with st.empty():
                        self.countdown_v2(datetime_question_started)
                else:
                    if st.session_state.user_answer is not None:
                        st.success('we got your answer 🙂')
                    else:
                        st.error("You didn't submit your answer 😢")

                    with st.spinner("Waiting for Host"):
                        time.sleep(3)

            st.session_state.current_session_status, st.session_state.index_questions_df, st.session_state.playing_at = self.get_current_session_state()
            placeholder.empty()
            st.rerun()
        elif st.session_state.current_session_status == 'playing_again':
            st.session_state.keep_playing = True
            self.next_page('waiting_page')
        else:
            if (st.session_state.current_session_status == 'waiting'):
                self.send_user_answer_by_question(datetime_question_started)
            self.next_page("waiting_page")

    def send_user_answer_by_question(self, datetime_question_started):
        if not st.session_state.boolean_unique_answer_send:
            SQL = self.cmd_insert_game_answer.format(
                st.session_state.user_id_logged_in,
                st.session_state.current_question_id,
                st.session_state.user_answer,
                datetime_question_started,
                st.session_state.game_code
            )
            # st.write(SQL)
            exe_sf(create_conn(), sql=SQL, return_as_df=False)
            st.session_state.disable_question_buttons = True
            if st.session_state.user_answer != st.session_state.current_question_correct_answer:
                st.session_state.keep_playing = False
                index_ = st.session_state.index_questions_df
            else:
                index_ = st.session_state.index_questions_df + 1

            SQL_2 = self.cmd_update_user_question_id.format(index_, st.session_state.user_id_logged_in)
            exe_sf(create_conn(), sql=SQL_2, return_as_df=False)

            st.session_state.index_questions_df += 1

            st.session_state.boolean_unique_answer_send = True

    def lose_page(self):
        st.header("Thanks for being an amazing part of this!")
        st.error("Sorry, it was not the answer")

        self.show_score()

    def simulate_answer(self, percentage, correct_A, incorrect_A):
        if not (0 <= percentage <= 100):
            raise ValueError("Percentage must be between 0 and 100.")

        # Generate a random number between 1 and 100
        random_value = random.randint(1, 100)

        if random_value <= percentage:
            return correct_A, incorrect_A  # Return the first answer (e.g., "1")
        else:
            return incorrect_A, correct_A  # Return the other answer (e.g., "0")

    def show_score(self):
        st.header("Score Table")
        css = """
            <style>
            .container {
                display: flex;
                flex-direction: column;
                gap: 0;  /* Reducing the gap between lines */
                max-width: 100%;
                background: linear-gradient(to bottom, #04104d, #1c0048);  /* Blue gradient */
                padding: 10px;  /* Adding some padding for visual spacing */
                border-radius: 8px;  /* Rounded corners for the background */
            }
            .container div:nth-child(5n+1) {
                color: #FFD700; /* Gold */
            }
            .container div:nth-child(5n+2) {
                color: white; /* Sky Blue */
            }
            .container div:nth-child(5n+3) {
                color: white; /* Light Pink */
            }
            .container div:nth-child(5n+4) {
                color: white; /* Light Green */
            }
            .container div:nth-child(5n+5) {
                color: white; /* OrangeRed */
            }
            .container div {
                padding: 0;  /* Removing extra padding */
                text-align: center;
                font-size: 24px;  /* Increasing text size */
                font-weight: bold;
                line-height: 1.1;  /* Reducing space between lines */
                border-radius: 8px;
            }
            </style>
        """

        # df = st.session_state.score_df.sort(by='SCORE_ID')
        total_questions = len(st.session_state.score_df)

        html = '<div class="container">'
        for ind, value_s in enumerate(st.session_state.score_df.itertuples()):
            val = '$' + format(value_s.SCORE, ",")
            if (total_questions - ind) == (st.session_state.index_questions_df + 1):
                html += f'<div style="background-color: gold; border: 1px white;">{val}</div>'
            elif (total_questions - ind) <= st.session_state.index_questions_df:
                html += f"<div><s>{val}</s></div>"  # Each score in its own <div> to apply colors based on position
            else:
                html += f"<div>{val}</div>"  # Each score in its own <div> to apply colors based on position
        html += "</div>"

        # Render the CSS and the HTML in the Streamlit app
        st.markdown(css, unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

    def waiting_page(self):
        #time.sleep(1)
        st.session_state.question_time_left = None
        st.session_state.datetime_question_target = None
        st.session_state.wildcard_50_50_act = False
        st.session_state.wildcard_audience_act = False
        st.session_state.wildcard_phone_act = False

        st.session_state.boolean_unique_answer_send = False

        st.session_state.get_datetime_question_started = True
        # st.session_state.timer_display = True
        st.session_state.answer_text = ''  # Reset the answer text
        st.session_state.disable_question_buttons = False

        st.session_state.last_page = 'waiting_page'

        if st.session_state.index_questions_df >= 4:
            st.session_state.show_wildcards = True

        if st.session_state.current_session_status not in ('finished', 'playing'):
            st.session_state.current_session_status, st.session_state.index_questions_df, st.session_state.playing_at = self.get_current_session_state()
        # st.write(session_status)
        if (st.session_state.current_session_status == 'waiting') | (st.session_state.current_session_status == 'lobby'):
            placeholder = st.empty()
            with placeholder.container():
                st.markdown(
                    """
                    <h1 style='text-align: center;'>Waiting Room</h1>
                    """,
                    unsafe_allow_html=True)

                if (st.session_state.keep_playing) & (st.session_state.index_questions_df > 0):
                    random_success_message = random.choice(self.list_correct_ans)

                    st.success(random_success_message)
                    if st.session_state.congrats_waiting_room:
                        st.balloons()
                        st.session_state.congrats_waiting_room = False

                elif (st.session_state.keep_playing == False) & (st.session_state.index_questions_df > 0):
                    self.next_page("lose_page")

                col1, col2 = st.columns(2)

                with col2:
                    # st.write('Table here')
                    self.show_score()
                with col1:
                    st.header("Waiting Room")
                    with st.status("Waiting"):
                        time.sleep(5)
                        st.write("Waiting for Host")

                # st.write('Rerunning')
            st.session_state.current_session_status, st.session_state.index_questions_df, st.session_state.playing_at = self.get_current_session_state()
            placeholder.empty()
            st.rerun()
        elif (st.session_state.current_session_status == 'finished'):
            time.sleep(10)
            self.next_page('add_code_page')
        elif (st.session_state.current_session_status == 'playing'):
            self.next_page("question_page")

    def final_results_page(self):
        st.balloons()
        st.header("YOU ARE THE WINNER!!!")
        st.subheader("🥳🥳🥳")

    def run(self):
        if st.session_state.debug:
            st.session_state.current_page = "register_page"
        # st.write(st.session_state.current_page)

        if st.session_state.current_page == "add_code_page":
            self.add_code_page()
        elif st.session_state.current_page == "register_page":
            self.register_page()
        elif st.session_state.current_page == "question_page":
            self.question_page()
        elif st.session_state.current_page == "waiting_page":
            self.waiting_page()
        elif st.session_state.current_page == "lose_page":
            self.lose_page()
        elif st.session_state.current_page == 'final_results_page':
            self.final_results_page()


app = UserGUI()
app.run()
