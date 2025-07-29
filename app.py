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

# class_student_management.py (app.py의 일부로 사용 가능)
import streamlit as st
import pandas as pd

# Firestore와 Storage는 app.py에서 초기화된 db, bucket 사용

# 수업 관리
if menu == "수업 관리":
    st.header("🗂️ 수업 관리")
    tab1, tab2 = st.tabs(["📋 수업 목록 조회", "➕ 수업 등록"])

    with tab1:
        classes = db.collection("classes").stream()
        rows = []
        for c in classes:
            d = c.to_dict()
            rows.append({
                "학년도": d.get("year"),
                "학기": d.get("semester"),
                "교과": d.get("subject_name"),
                "반": d.get("classroom"),
                "요일": ", ".join(d.get("days", [])),
                "교시": ", ".join(map(str, d.get("periods", [])))
            })
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("등록된 수업이 없습니다.")

    with tab2:
        with st.form("class_form"):
            year = st.selectbox("학년도", list(range(2020, 2031)), index=5)
            semester = st.selectbox("학기", [1, 2])

            subjects = db.collection("subjects").stream()
            subject_list = [(s.id, s.to_dict().get("name")) for s in subjects]
            subject_dict = {name: id_ for id_, name in subject_list}
            subject_name = st.selectbox("교과 선택", list(subject_dict.keys()))

            classroom = st.text_input("수업 학반")
            days = st.multiselect("수업 요일", ["월", "화", "수", "목", "금"])
            periods = st.multiselect("수업 교시", list(range(1, 11)))

            submitted = st.form_submit_button("수업 등록")

            if submitted and classroom and days and periods:
                db.collection("classes").add({
                    "year": year,
                    "semester": semester,
                    "subject_id": subject_dict[subject_name],
                    "subject_name": subject_name,
                    "classroom": classroom,
                    "days": days,
                    "periods": periods
                })
                st.success("수업이 등록되었습니다.")
            elif submitted:
                st.warning("모든 필드를 입력해주세요.")

# 학생 관리
elif menu == "학생 관리":
    st.header("👨‍🎓 학생 관리")
    class_docs = db.collection("classes").stream()
    class_options = [(doc.id, f"{doc.to_dict()['year']}학년도 {doc.to_dict()['semester']}학기 {doc.to_dict()['classroom']}") for doc in class_docs]
    class_dict = {label: id_ for id_, label in class_options}

    selected_class = st.selectbox("수업반 선택", list(class_dict.keys()))
    if selected_class is not None:
        class_id = class_dict[selected_class]
        class_id = class_dict[selected_class]
    else:
        st.warning("수업을 선택해주세요.")

    subtab1, subtab2 = st.tabs(["➕ 학생 추가", "📑 학생 목록"])

    with subtab1:
        method = st.radio("등록 방식", ["직접 입력", "CSV 업로드"])

        if method == "직접 입력":
            with st.form("manual_student"):
                sid = st.text_input("학번")
                name = st.text_input("이름")
                submit_student = st.form_submit_button("학생 등록")
                if submit_student and sid and name:
                    db.collection("classes").document(class_id).collection("students").add({
                        "sid": sid,
                        "name": name
                    })
                    st.success("학생이 등록되었습니다.")

        else:
            file = st.file_uploader("CSV 업로드 (학번,sid / 이름,name)", type="csv")
            if file:
                df = pd.read_csv(file)
                for _, row in df.iterrows():
                    db.collection("classes").document(class_id).collection("students").add({
                        "sid": str(row['sid']),
                        "name": row['name']
                    })
                st.success(f"{len(df)}명 학생이 등록되었습니다.")

    with subtab2:
        students = db.collection("classes").document(class_id).collection("students").stream()
        student_data = [s.to_dict() for s in students]
        if student_data:
            st.dataframe(pd.DataFrame(student_data))
        else:
            st.info("등록된 학생이 없습니다.")


