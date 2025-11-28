import streamlit as st

# Série
exercises = st.multiselect("Exercise:", ["Curl", "Bench Press"])
weight = st.number_input("Weight: ", min_value=0)
reps = st.number_input("Reps: ", min_value=0)
reps_in_reserve = st.number_input("RIR: ", min_value=0)
