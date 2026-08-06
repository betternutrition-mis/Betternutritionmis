df_mil_saved.drop(columns=["id"])
        if "id" in df_mil_saved.columns
        else df_mil_saved,
        use_container_width=True,
    )

    st.subheader("Saved Quality Lab Records")
    df_q_saved = load_data("quality")
    if not df_q_saved.empty:
        st.dataframe(
            df_q_saved.drop(columns=["id", "milling_id"])
            if "id" in df_q_saved.columns
            else df_q_saved,
            use_container_width=True,
        )

elif menu == "3. Finished Goods & Yield":
    st.header("Finished Goods Production & Yield Tracking")
    df_mil = load_data("milling")
    if df_mil.empty:
        st.warning(
            "Pehle Menu 2 se Milling entry karein, tabhi Finished Goods entry"
            " ho sakegi."
        )
    else:
        df_mil["label"] = (
            "ID: "
            + df_mil["id"].astype(str)
            + " | Miller: "
            + df_mil["miller_name"]
            + " | Date: "
            + df_mil["milling_date"]
            + " | Qty: "
            + df_mil["milling_qty"].astype(str)
            + " kg"
        )
        sel_milling = st.selectbox(
            "Select Milling Batch for Finished Goods", df_mil["label"].tolist()
        )
        row_mil = df_mil[df_mil["label"] == sel_milling].iloc[0]
        milling_id = int(row_mil["id"])
        miller_name = row_mil["miller_name"]
        milling_qty = float(row_mil["milling_qty"])

        with st.form("fg_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                production_date = str(
                    st.date_input("Production Date", datetime.date.today())
                )
                mfd_date = st.text_input("MFD Date", placeholder="e.g. June 2026")
                expiry_date = st.text_input(
                    "Expiry Date", placeholder="e.g. 6 Months"
                )
            with c2:
                mrp = st.number_input("MRP (Rs)", min_value=0.0, value=0.0)
                product_code = st.text_input(
                    "Product Code / SKU", value="BN-ATTA-01"
                )
                pouch_500g = st.number_input(
                    "500g Pouches Count", min_value=0, value=0, step=1
                )
            with c3:
                pouch_1kg = st.number_input(
                    "1kg Pouches Count", min_value=0, value=0, step=1
                )
                pouch_2kg = st.number_input(
                    "2kg Pouches Count", min_value=0, value=0, step=1
                )
                pouch_5kg = st.number_input(
                    "5kg Pouches Count", min_value=0, value=0, step=1
                )

            st.divider()
            sc1, sc2 = st.columns(2)
            with sc1:
                bran_qty = st.number_input(
                    "Bran Quantity (kg)", min_value=0.0, value=0.0, step=1.0
                )
            with sc2:
                refraction_qty = st.number_input(
                    "Refraction Quantity (kg)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                )

            submit_fg = st.form_submit_button(
                label="Calculate Yield & Save Finished Goods"
            )
            if submit_fg:
                wt_500g = pouch_500g * 0.5
                wt_1kg = pouch_1kg * 1.0
                wt_2kg = pouch_2kg * 2.0
                wt_5kg = pouch_5kg * 5.0
                total_finished_qty = wt_500g + wt_1kg + wt_2kg + wt_5kg

                bran_pct = (
                    (bran_qty / milling_qty) * 100 if milling_qty > 0 else 0.0
                )
                refraction_pct = (
                    (refraction_qty / milling_qty) * 100
                    if milling_qty > 0
                    else 0.0
                )
                yield_pct = (
                    (total_finished_qty / milling_qty) * 100
                    if milling_qty > 0
                    else 0.0
                )

                total_accounted = (
                    total_finished_qty + bran_qty + refraction_qty
                )
                processing_loss_qty = milling_qty - total_accounted
                processing_loss_pct = (
                    (processing_loss_qty / milling_qty) * 100
                    if milling_qty > 0
                    else 0.0
                )

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO finished_goods (milling_id, production_date, miller_name, mfd_date, expiry_date, mrp, product_code, pouch_500g, pouch_1kg, pouch_2kg, pouch_5kg, total_finished_qty, bran_qty, bran_pct, refraction_qty, refraction_pct, yield_pct, processing_loss_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        milling_id,
                        production_date,
                        miller_name,
                        mfd_date,
                        expiry_date,
                        mrp,
                        product_code,
                        pouch_500g,
                        pouch_1kg,
                        pouch_2kg,
                        pouch_5kg,
                        round(total_finished_qty, 2),
                        bran_qty,
                        f"{bran_pct:.2f}%",
                        refraction_qty,
                        f"{refraction_pct:.2f}%",
                        f"{yield_pct:.2f}%",
                        f"{processing_loss_pct:.2f}%",
                    ),
                )
                conn.commit()
                conn.close()
                st.success(
                    f"Finished Goods Saved! Total Finished Output:"
                    f" {total_finished_qty:,.2f} kg | Yield:"
                    f" {yield_pct:.2f}%"
                )

    st.subheader("Saved Finished Goods Records")
    df_fg_saved = load_data("finished_goods")
    if not df_fg_saved.empty:
        st.dataframe(
            df_fg_saved.drop(columns=["id", "milling_id"])
            if "id" in df_fg_saved.columns
            else df_fg_saved,
            use_container_width=True,
        )

elif menu == "4. Better Nutrition Packing Material":
    st.header("Better Nutrition Packing Material Dispatch/Stock Entry")
    miller_name = get_miller_input("pm")
    with st.form("pm_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            pm_date = str(st.date_input("Date", datetime.date.today()))
            carton_type = st.selectbox(
                "Carton Type", ["500g Carton", "1kg Carton", "2kg Carton", "5kg Carton"]
            )
            cartons_sent = st.number_input(
                "Cartons Sent (Units)", min_value=0, value=0, step=1
            )
            tape_sent = st.number_input(
                "Tape Sent (Rolls)", min_value=0, value=0, step=1
            )
        with c2:
            oxysorb_qty = st.number_input(
                "Oxysorb Packets Qty", min_value=0, value=0, step=10
            )
            roll_sku = st.text_input("Roll SKU / Description", value="")
            roll_qty_sent = st.number_input(
                "Roll Qty Sent (kg or meters)",
                min_value=0.0,
                value=0.0,
                step=1.0,
            )

        submit_pm = st.form_submit_button(
            label="Save Packing Material Entry"
        )
        if submit_pm:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO packing_material (date, miller_name, carton_type, cartons_sent, tape_sent, oxysorb_qty, roll_sku, roll_qty_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pm_date,
                    miller_name,
                    carton_type,
                    cartons_sent,
                    tape_sent,
                    oxysorb_qty,
                    roll_sku,
                    roll_qty_sent,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Packing Material entry successfully saved for {miller_name}!"
            )

    st.subheader("Saved Packing Material Records")
    df_pm_saved = load_data("packing_material")
    if not df_pm_saved.empty:
        st.dataframe(
            df_pm_saved.drop(columns=["id"])
            if "id" in df_pm_saved.columns
            else df_pm_saved,
            use_container_width=True,
        )

elif menu == "5. Daily Dispatch Entry":
    st.header("Daily Finished Goods Dispatch Entry")
    miller_name = get_miller_input("dispatch")
    with st.form("dispatch_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            dispatch_date = str(
                st.date_input("Dispatch Date", datetime.date.today())
            )
            vehicle_no = st.text_input(
                "Vehicle Number", placeholder="e.g. UP-32-XZ-1234"
            )
            disp_500g = st.number_input(
                "Dispatched 500g Pouches", min_value=0, value=0, step=1
            )
            disp_1kg = st.number_input(
                "Dispatched 1kg Pouches", min_value=0, value=0, step=1
            )
        with c2:
            disp_2kg = st.number_input(
                "Dispatched 2kg Pouches", min_value=0, value=0, step=1
            )
            disp_5kg = st.number_input(
                "Dispatched 5kg Pouches", min_value=0, value=0, step=1
            )
            cartons_used = st.number_input(
                "Cartons Used", min_value=0, value=0, step=1
            )
            remarks = st.text_input("Dispatch Remarks / Destination", value="")

        submit_disp = st.form_submit_button(
            label="Save Dispatch Entry"
        )
        if submit_disp:
            total_disp_wt = (
                (disp_500g * 0.5)
                + (disp_1kg * 1.0)
                + (disp_2kg * 2.0)
                + (disp_5kg * 5.0)
            )
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dispatch (dispatch_date, miller_name, vehicle_no, disp_500g, disp_1kg, disp_2kg, disp_5kg, total_dispatched_wt, cartons_used, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    dispatch_date,
                    miller_name,
                    vehicle_no,
                    disp_500g,
                    disp_1kg,
                    disp_2kg,
                    disp_5kg,
                    round(total_disp_wt, 2),
                    cartons_used,
                    remarks,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Dispatch Saved Successfully! Total Dispatched Weight:"
                f" {total_disp_wt:,.2f} kg"
            )

    st.subheader("Saved Dispatch Records")
    df_disp_saved = load_data("dispatch")
    if not df_disp_saved.empty:
        st.dataframe(
            df_disp_saved.drop(columns=["id"])
            if "id" in df_disp_saved.columns
            else df_disp_saved,
            use_container_width=True,
        )

elif menu == "6. Master Records & Export (Admin Controls)":
    st.header("Master Records, Data Management & Admin Controls")

    if user_role != "Admin":
        st.warning(
            "⚠️ Ye section sirf **Admin** access ke liye hai. Aapka current role"
            f" '{user_role}' hai."
        )
    else:
        st.success(
            "🔓 Admin privileges active. Aap tables view kar sakte hain aur data"
            " export/delete kar sakte hain."
        )

        table_to_manage = st.selectbox(
            "Select Database Table to Manage",
            [
                "raw_material",
                "milling",
                "quality",
                "finished_goods",
                "packing_material",
                "dispatch",
            ],
        )

        df_manage = load_data(table_to_manage)
        st.write(f"### Current Data in `{table_to_manage}`")
        if df_manage.empty:
            st.info("Table khaali hai.")
        else:
            st.dataframe(df_manage, use_container_width=True)

            # CSV Download Button
            csv_data = df_manage.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download `{table_to_manage}` as CSV",
                data=csv_data,
                file_name=f"{table_to_manage}_export.csv",
                mime="text/csv",
            )

        st.divider()
        st.subheader("Danger Zone / Database Maintenance")
        if st.button("🗑️ Delete Database File (Reset Everything)"):
            if os.path.exists("flour_mill_erp.db"):
                os.remove("flour_mill_erp.db")
                st.warning(
                    "Database file delete ho chuki hai. App ko refresh karein"
                    " naye tables banane ke liye."
                )
                st.rerun()
            else:
                st.error("Database file nahi mili.")
