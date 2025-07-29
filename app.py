import streamlit as st

st.title("앱개발 연수 중")
st.header("파이참 설치 실습 중...스트림릿 클라우드와 연동...")

# app.py
import streamlit as st
from firebase_admin import credentials, initialize_app
from firebase_admin import firestore, storage
import pandas as pd
import datetime


# Firebase 초기화
@st.cache_resource
def init_firebase():
    cred = credentials.Certificate("firebase_service_account.json")  # Firebase 서비스 계정 키
    initialize_app(cred, {'storageBucket': 'YOUR_FIREBASE_PROJECT.appspot.com'})
    return firestore.client(), storage.bucket()

db, bucket = init_firebase()

# 사이드바 메뉴
menu = st.sidebar.selectbox("메뉴 선택", [
    "대시보드",
    "교과 관리",
    "수업 관리",
    "학생 관리",
    "진도 및 특기사항 기록",
    "출결 관리"
])

# 1. 대시보드
if menu == "대시보드":
    st.header("📊 대시보드")
    today = datetime.date.today()
    st.write(f"오늘 날짜: {today}")
    # TODO: 전체 수업반 진도 및 출결 요약 출력

# 2. 교과 관리
elif menu == "교과 관리":
    st.header("📚 교과 관리")
    tab1, tab2 = st.tabs(["📄 교과 목록 조회", "➕ 교과 추가"])

    with tab1:
        docs = db.collection("subjects").stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            data.append({
                "교과명": d.get("name"),
                "학년도": d.get("year"),
                "학기": d.get("semester"),
                "PDF 링크": d.get("pdf_url")
            })
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("등록된 교과가 없습니다.")

    with tab2:
        with st.form("subject_form"):
            name = st.text_input("교과명")
            year = st.selectbox("학년도", list(range(2020, 2031)), index=5)
            semester = st.selectbox("학기", [1, 2])
            file = st.file_uploader("PDF 파일 업로드 (10MB 이하)", type="pdf")
            submitted = st.form_submit_button("교과 등록")

            if submitted:
                if not name or not file:
                    st.warning("모든 필드를 입력해주세요.")
                elif file.size > 10 * 1024 * 1024:
                    st.error("파일 용량이 10MB를 초과했습니다.")
                else:
                    blob_path = f"subject_plans/{name}_{year}_{semester}.pdf"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_file(file, content_type="application/pdf")
                    pdf_url = blob.public_url

                    db.collection("subjects").add({
                        "name": name,
                        "year": year,
                        "semester": semester,
                        "pdf_url": pdf_url
                    })
                    st.success("교과가 성공적으로 등록되었습니다.")

# 3~6번 메뉴는 이후 구현 예정
else:
    st.warning(f"'{menu}' 기능은 아직 구현되지 않았습니다. 다음 단계에서 개발을 계속하세요.")
