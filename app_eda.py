import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **지역별 인구 분석 웹앱**

        - 데이터 출처: 통계청 (수정된 샘플 데이터 사용)
        - 설명: 연도별·지역별 인구, 출생아수, 사망자수 등 통계를 시각화하고 분석하는 웹 애플리케이션입니다.
        - 주요 변수:
          - `연도`: 기준 연도
          - `지역`: 전국 또는 시도 단위 지역명
          - `인구`: 총 인구 수
          - `출생아수(명)`: 해당 연도의 출생자 수
          - `사망자수(명)`: 해당 연도의 사망자 수
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()
        
# ---------------------
# EDA 페이지 클래스 (수정 완료)
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 인구 통계 EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드 해주세요.")
            return

        # 데이터 불러오기 및 전처리
        df = pd.read_csv(uploaded)
        st.subheader("df.info()")
        buffer = io.StringIO()
        df.info(buf=buffer)
        st.text(buffer.getvalue())
        
        df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
        df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')
        df['자연증가율'] = df['출생아수(명)'] - df['사망자수(명)']

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 품질 점검",
            "4. 인구 시각화",
            "5. 자연 증가율 분석",
            "6. 인구 감소/고령화 경향"
        ])

        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
                - 인구 통계를 통해 지역별 인구 변화와 출생/사망 동향을 분석합니다.  
                - 이를 통해 고령화 속도, 인구 감소 문제 등을 탐색합니다.

                **분석 절차**  
                1. 데이터 구조 확인  
                2. 전처리 및 품질 점검  
                3. 연도별/지역별 인구 변화 시각화  
                4. 출생/사망을 통한 자연 증가율 분석  
                5. 지역별 인구 감소 경향 또는 고령화 관련 지표 분석
            """)

        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"""
                - 총 행 수: {df.shape[0]}  
                - 주요 변수:  
                  - **연도**: 연도  
                  - **지역**: 전국 또는 시도 단위  
                  - **인구**: 해당 연도·지역의 총 인구  
                  - **출생아수(명)**: 출생 수  
                  - **사망자수(명)**: 사망 수
            """)
            st.subheader("기초 통계량")
            st.dataframe(df.describe())
            st.subheader("데이터 샘플")
            st.dataframe(df.head())

        with tabs[2]:
            st.header("🧹 품질 점검")
            st.subheader("결측값 확인")
            st.write(df.isnull().sum())
            st.subheader("중복 확인")
            st.write(f"중복 행 개수: {df.duplicated().sum()}개")

        with tabs[3]:
            st.header("📈 연도별/지역별 인구 시각화")
            regions = df['지역'].unique().tolist()
            selected = st.multiselect("지역 선택", regions, default=["전국"])
            filtered = df[df['지역'].isin(selected)]
            fig, ax = plt.subplots()
            sns.lineplot(data=filtered, x='연도', y='인구', hue='지역', marker="o", ax=ax)
            ax.set_ylabel("인구 수")
            st.pyplot(fig)

        with tabs[4]:
            st.header("👶 자연 증가율 (출생 - 사망)")
            fig2, ax2 = plt.subplots()
            sns.lineplot(data=df[df['지역'] == '전국'], x='연도', y='자연증가율', marker="o", ax=ax2)
            ax2.axhline(0, color='gray', linestyle='--')
            ax2.set_ylabel("자연 증가 인구 수")
            st.pyplot(fig2)

        with tabs[5]:
            st.header("⚠️ 지역별 인구 감소 경향")
            latest_year = df['연도'].max()
            past_year = df['연도'].min()

            df_latest = df[df['연도'] == latest_year]
            df_past = df[df['연도'] == past_year]
            merged = pd.merge(df_latest, df_past, on="지역", suffixes=('_최신', '_과거'))
            merged['인구감소율(%)'] = ((merged['인구_최신'] - merged['인구_과거']) / merged['인구_과거']) * 100

            st.subheader(f"{past_year}년 대비 {latest_year}년 인구감소율")
            st.dataframe(merged[['지역', '인구감소율(%)']].sort_values(by='인구감소율(%)'))

            fig3, ax3 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=merged, x='지역', y='인구감소율(%)', ax=ax3)
            ax3.axhline(0, color='gray', linestyle='--')
            plt.xticks(rotation=45)
            st.pyplot(fig3)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()