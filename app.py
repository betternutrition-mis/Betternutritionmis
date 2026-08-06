elif menu == "2. Milling & Quality Lab Entry":
    st.header("Milling Processing & Quality Lab Entry")

    if "edit_mil_id" not in st.session_state:
        st.session_state["edit_mil_id"] = None

    df_mil_saved = load_data("milling")

    action_type_mil = "➕ New Milling & Quality Entry"
    if not df_mil_saved.empty:
        action_type_mil = st.radio(
            "Action Mode", ["➕ New Milling & Quality Entry", "✏️ Edit / 🗑️ Delete Existing Milling", "🛠️ Update Quality for Old Batches"], horizontal=True, key="mode_mil"
        )
    else:
        action_type_mil = st.radio(
            "Action Mode", ["➕ New Milling & Quality Entry", "🛠️ Update Quality for Old Batches"], horizontal=True, key="mode_mil_empty"
        )

    edit_mil_data = None
    if action_type_mil == "✏️ Edit / 🗑️ Delete Existing Milling" and not df_mil_saved.empty:
        df_mil_saved["label"] = (
            "ID: " + df_mil_saved["id"].astype(str) + " | " + df_mil_saved["miller_name"] + " (" + df_mil_saved["milling_date"] + ")"
        )
        sel_edit_mil = st.selectbox("Select Milling Record to Modify/Delete", df_mil_saved["label"].tolist(), key="sel_edit_mil")
        selected_mil_row = df_mil_saved[df_mil_saved["label"] == sel_edit_mil].iloc[0]
        st.session_state["edit_mil_id"] = int(selected_mil_row["id"])
        edit_mil_data = selected_mil_row

        with st.expander("⚠️ Delete Confirmation Box (Milling)", expanded=False):
            confirm_del_mil = st.checkbox("Haan, main is milling record ko permanently delete karna chahta hoon", key="conf_del_mil")
            if st.button("🗑️ Confirm & Delete Milling Record", type="primary", key="btn_del_mil_rec"):
                if confirm_del_mil:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM milling WHERE id = ?", (st.session_state["edit_mil_id"],))
                    cursor.execute("DELETE FROM quality WHERE milling_id = ?", (st.session_state["edit_mil_id"],))
                    conn.commit()
                    conn.close()
                    st.success(f"Milling & Quality Record ID {st.session_state['edit_mil_id']} deleted successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    elif action_type_mil == "🛠️ Update Quality for Old Batches":
        st.subheader("Update/Add Quality Parameters for Existing Milling Batches")
        if df_mil_saved.empty:
            st.warning("Koi milling batch available nahi hai.")
        else:
            df_mil_saved["label"] = (
                "ID: " + df_mil_saved["id"].astype(str) + " | " + df_mil_saved["miller_name"] + " (" + df_mil_saved["milling_date"] + ")"
            )
            sel_q_batch = st.selectbox("Select Milling Batch for Quality", df_mil_saved["label"].tolist(), key="sel_q_batch_old")
            q_row = df_mil_saved[df_mil_saved["label"] == sel_q_batch].iloc[0]
            q_milling_id = int(q_row["id"])
            q_miller = q_row["miller_name"]

            df_q_existing = load_data("quality")
            q_match = df_q_existing[df_q_existing["milling_id"] == q_milling_id]
            q_exist_data = q_match.iloc[0] if not q_match.empty else None

            with st.form("old_quality_form"):
                st.write(f"**Quality Lab Test Entry for Batch ID:** {q_milling_id} ({q_miller})")
                c1, c2, c3 = st.columns(3)
                with c1:
                    q_date_val = datetime.date.today()
                    if q_exist_data is not None and pd.notna(q_exist_data["test_date"]):
                        try:
                            q_date_val = datetime.datetime.strptime(q_exist_data["test_date"], "%d %b %Y").date()
                        except Exception:
                            pass
                    test_date = st.date_input("Lab Test Date", value=q_date_val, key="old_tdate").strftime("%d %b %Y")

                    def_mo_milled = float(q_exist_data["moisture_milled"]) if q_exist_data is not None and pd.notna(q_exist_data["moisture_milled"]) else 0.0
                    moisture_milled = st.number_input("Moisture % (Milled/Atta)", min_value=0.0, value=def_mo_milled, step=0.1, format="%.1f", key="old_mo_milled")

                    def_gran = str(q_exist_data["granulation"]) if q_exist_data is not None and pd.notna(q_exist_data["granulation"]) else ""
                    granulation = st.text_input("Granulation / Fineness", value=def_gran, placeholder="e.g. Fine / 95% through 150 mesh", key="old_gran")

                with c2:
                    def_ccl4 = str(q_exist_data["ccl4"]) if q_exist_data is not None and pd.notna(q_exist_data["ccl4"]) else ""
                    ccl4 = st.text_input("CCL4 Test", value=def_ccl4, placeholder="e.g. Sound / Clean", key="old_ccl4")

                    def_ash = float(q_exist_data["ash_aia"]) if q_exist_data is not None and pd.notna(q_exist_data["ash_aia"]) else 0.0
                    ash_aia = st.number_input("Ash / AIA %", min_value=0.0, value=def_ash, step=0.01, format="%.2f", key="old_ash")

                    def_aa = float(q_exist_data["alcoholic_acidity"]) if q_exist_data is not None and pd.notna(q_exist_data["alcoholic_acidity"]) else 0.0
                    alcoholic_acidity = st.number_input("Alcoholic Acidity", min_value=0.0, value=def_aa, step=0.01, format="%.2f", key="old_aa")

                with c3:
                    def_wap = float(q_exist_data["wap"]) if q_exist_data is not None and "wap" in q_exist_data and pd.notna(q_exist_data["wap"]) else 0.0
                    wap = st.number_input("WAP (Water Absorption / Wapsi)", min_value=0.0, value=def_wap, step=0.1, format="%.1f", key="old_wap")

                    def_gluten = str(q_exist_data["gluten"]) if q_exist_data is not None and pd.notna(q_exist_data["gluten"]) else ""
                    gluten = st.text_input("Gluten %", value=def_gluten, placeholder="e.g. 9.5%", key="old_gluten")

                    def_chapati = str(q_exist_data["chapati_sensory"]) if q_exist_data is not None and pd.notna(q_exist_data["chapati_sensory"]) else ""
                    chapati_sensory = st.text_input("Chapati Sensory / Quality", value=def_chapati, placeholder="e.g. Soft, Excellent", key="old_chap")

                submit_old_q = st.form_submit_button("💾 Save / Update Quality Lab Data")
                if submit_old_q:
                    conn = get_connection()
                    cursor = conn.cursor()
                    if q_exist_data is not None:
                        cursor.execute("""
                            UPDATE quality 
                            SET test_date=?, miller_name=?, moisture_milled=?, granulation=?, ccl4=?, ash_aia=?, alcoholic_acidity=?, wap=?, gluten=?, chapati_sensory=?
                            WHERE milling_id=?
                        """, (test_date, q_miller, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory, q_milling_id))
                    else:
                        cursor.execute("""
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (q_milling_id, test_date, q_miller, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory))
                    conn.commit()
                    conn.close()
                    st.success(f"Quality details successfully updated for Batch ID {q_milling_id}!")
                    st.rerun()

    if action_type_mil == "➕ New Milling & Quality Entry" or st.session_state["edit_mil_id"] is not None:
        def_mil_miller = edit_mil_data["miller_name"] if edit_mil_data is not None else None
        milling_miller_name = get_miller_input("mil", def_mil_miller)

        with st.form("milling_quality_form"):
            st.subheader("1. Milling Details")
            c1, c2, c3 = st.columns(3)
            with c1:
                def_mdate = datetime.date.today()
                if edit_mil_data is not None:
                    try:
                        def_mdate = datetime.datetime.strptime(edit_mil_data["milling_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                m_date_obj = st.date_input("Milling Date", value=def_mdate)
                milling_date = m_date_obj.strftime("%d %b %Y")
            with c2:
                def_mqty = float(edit_mil_data["milling_qty"]) if edit_mil_data is not None else 0.0
                milling_qty = st.number_input("Milling Quantity (Wheat Input kg)", min_value=0.0, value=def_mqty, step=10.0, format="%.2f")
            with c3:
                def_temp_time = edit_mil_data["tempering_time"] if edit_mil_data is not None and "tempering_time" in edit_mil_data else ""
                tempering_time = st.text_input("Tempering Time", value=def_temp_time, placeholder="e.g. 12 Hours")

            def_temp_water = float(edit_mil_data["tempering_water"]) if edit_mil_data is not None and "tempering_water" in edit_mil_data and pd.notna(edit_mil_data["tempering_water"]) else 0.0
            tempering_water = st.number_input("Tempering Water Added (liters/kg)", min_value=0.0, value=def_temp_water, step=1.0)

            st.divider()
            st.subheader("2. Quality Lab Parameters (Optional for New Entry)")

            q_edit_data = None
            if st.session_state["edit_mil_id"] is not None:
                df_q_check = load_data("quality")
                q_match_edit = df_q_check[df_q_check["milling_id"] == st.session_state["edit_mil_id"]]
                if not q_match_edit.empty:
                    q_edit_data = q_match_edit.iloc[0]

            qc1, qc2, qc3 = st.columns(3)
            with qc1:
                def_tdate = datetime.date.today()
                if q_edit_data is not None and pd.notna(q_edit_data["test_date"]):
                    try:
                        def_tdate = datetime.datetime.strptime(q_edit_data["test_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                q_test_date = st.date_input("Lab Test Date", value=def_tdate).strftime("%d %b %Y")

                def_mm = float(q_edit_data["moisture_milled"]) if q_edit_data is not None and pd.notna(q_edit_data["moisture_milled"]) else 0.0
                moisture_milled = st.number_input("Moisture % (Milled/Atta)", min_value=0.0, value=def_mm, step=0.1, format="%.1f")

                def_gran = str(q_edit_data["granulation"]) if q_edit_data is not None and pd.notna(q_edit_data["granulation"]) else ""
                granulation = st.text_input("Granulation / Fineness", value=def_gran, placeholder="e.g. Fine / 95% through 150 mesh")
            with qc2:
                def_ccl4 = str(q_edit_data["ccl4"]) if q_edit_data is not None and pd.notna(q_edit_data["ccl4"]) else ""
                ccl4 = st.text_input("CCL4 Test", value=def_ccl4, placeholder="e.g. Sound / Clean")

                def_ash = float(q_edit_data["ash_aia"]) if q_edit_data is not None and pd.notna(q_edit_data["ash_aia"]) else 0.0
                ash_aia = st.number_input("Ash / AIA %", min_value=0.0, value=def_ash, step=0.01, format="%.2f")

                def_aa = float(q_edit_data["alcoholic_acidity"]) if q_edit_data is not None and pd.notna(q_edit_data["alcoholic_acidity"]) else 0.0
                alcoholic_acidity = st.number_input("Alcoholic Acidity", min_value=0.0, value=def_aa, step=0.01, format="%.2f")
            with qc3:
                def_wap = float(q_edit_data["wap"]) if q_edit_data is not None and "wap" in q_edit_data and pd.notna(q_edit_data["wap"]) else 0.0
                wap = st.number_input("WAP (Water Absorption / Wapsi)", min_value=0.0, value=def_wap, step=0.1, format="%.1f")

                def_gluten = str(q_edit_data["gluten"]) if q_edit_data is not None and pd.notna(q_edit_data["gluten"]) else ""
                gluten = st.text_input("Gluten %", value=def_gluten, placeholder="e.g. 9.5%")

                def_chapati = str(q_edit_data["chapati_sensory"]) if q_edit_data is not None and pd.notna(q_edit_data["chapati_sensory"]) else ""
                chapati_sensory = st.text_input("Chapati Sensory / Quality", value=def_chapati, placeholder="e.g. Soft, Excellent")

            btn_mil_label = "Update Milling & Quality Record" if st.session_state["edit_mil_id"] is not None else "Save Milling & Quality Entry"
            submit_mil_q = st.form_submit_button(label=btn_mil_label)

            if submit_mil_q:
                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_mil_id"] is not None:
                    m_id = st.session_state["edit_mil_id"]
                    cursor.execute("""
                        UPDATE milling 
                        SET milling_date=?, miller_name=?, milling_qty=?, tempering_time=?, tempering_water=?
                        WHERE id=?
                    """, (milling_date, milling_miller_name, milling_qty, tempering_time, tempering_water, m_id))

                    cursor.execute("SELECT id FROM quality WHERE milling_id = ?", (m_id,))
                    q_exists = cursor.fetchone()
                    if q_exists:
                        cursor.execute("""
                            UPDATE quality 
                            SET test_date=?, miller_name=?, moisture_milled=?, granulation=?, ccl4=?, ash_aia=?, alcoholic_acidity=?, wap=?, gluten=?, chapati_sensory=?
                            WHERE milling_id=?
                        """, (q_test_date, milling_miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory, m_id))
                    else:
                        cursor.execute("""
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (m_id, q_test_date, milling_miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"Milling & Quality Record ID {m_id} Updated Successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO milling (milling_date, miller_name, milling_qty, tempering_time, tempering_water)
                        VALUES (?, ?, ?, ?, ?)
                    """, (milling_date, milling_miller_name, milling_qty, tempering_time, tempering_water))
                    new_milling_id = cursor.lastrowid

                    cursor.execute("""
                        INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_milling_id, q_test_date, milling_miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"Milling & Quality Entry Saved Successfully for {milling_miller_name}!")
                    st.rerun()

    st.subheader("Saved Milling & Quality Records")
    df_m_disp = load_data("milling")
    df_q_disp = load_data("quality")
    if not df_m_disp.empty:
        st.write("### Milling Entries Table")
        st.dataframe(df_m_disp, use_container_width=True)
    if not df_q_disp.empty:
        st.write("### Quality Lab Test Table (with WAP)")
        st.dataframe(df_q_disp, use_container_width=True)
