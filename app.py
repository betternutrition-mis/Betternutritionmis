elif menu == "3. Finished Goods & Yield":
    st.header("Finished Goods Production & Yield Tracking")

    if "edit_fg_id" not in st.session_state:
        st.session_state["edit_fg_id"] = None

    df_mil = load_data("milling")
    df_fg_existing = load_data("finished_goods")

    if df_mil.empty:
        st.warning("Pehle Menu 2 se Milling entry karein, tabhi Finished Goods entry ho sakegi.")
    else:
        action_type_fg = st.radio(
            "Action Mode", ["➕ New Finished Goods Entry", "✏️ Edit / 🗑️ Delete Existing Finished Goods"], horizontal=True, key="mode_fg"
        )

        edit_fg_data = None
        if action_type_fg == "✏️ Edit / 🗑️ Delete Existing Finished Goods" and not df_fg_existing.empty:
            df_fg_existing["label"] = (
                "ID: " + df_fg_existing["id"].astype(str) + " | " + df_fg_existing["miller_name"] + " | SKU: " + df_fg_existing["product_code"] + " (" + df_fg_existing["production_date"] + ")"
            )
            sel_fg_mod = st.selectbox("Select Finished Goods Record to Modify/Delete", df_fg_existing["label"].tolist(), key="sel_fg_mod")
            row_edit_fg = df_fg_existing[df_fg_existing["label"] == sel_fg_mod].iloc[0]
            st.session_state["edit_fg_id"] = int(row_edit_fg["id"])
            edit_fg_data = row_edit_fg

            with st.expander("⚠️ Delete Finished Goods Confirmation Box", expanded=False):
                confirm_del_fg = st.checkbox("Haan, main is finished goods record ko delete karna chahta hoon", key="conf_del_fg_rec")
                if st.button("🗑️ Confirm & Delete Finished Goods", type="primary", key="btn_del_fg_rec"):
                    if confirm_del_fg:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM finished_goods WHERE id = ?", (st.session_state["edit_fg_id"],))
                        conn.commit()
                        conn.close()
                        st.success("Finished Goods Record deleted successfully!")
                        st.session_state["edit_fg_id"] = None
                        st.rerun()
                    else:
                        st.error("Pehle confirmation checkbox par tick karein!")
        else:
            if action_type_fg != "✏️ Edit / 🗑️ Delete Existing Finished Goods":
                st.session_state["edit_fg_id"] = None

        if action_type_fg == "➕ New Finished Goods Entry" or st.session_state["edit_fg_id"] is not None:
            
            # Filtering logic to hide already completed milling batches for new entries
            if st.session_state["edit_fg_id"] is None and not df_fg_existing.empty and "milling_id" in df_fg_existing.columns:
                completed_milling_ids = df_fg_existing["milling_id"].tolist()
                df_mil_available = df_mil[~df_mil["id"].isin(completed_milling_ids)]
            else:
                df_mil_available = df_mil.copy()

            if st.session_state["edit_fg_id"] is None and df_mil_available.empty:
                st.success("🎉 Sabhi milling batches ki Finished Goods entry ki ja chuki hai!")
            else:
                if st.session_state["edit_fg_id"] is not None:
                    df_mil_available = df_mil.copy()

                df_mil_available["label"] = (
                    "Batch ID: "
                    + df_mil_available["id"].astype(str)
                    + " | "
                    + df_mil_available["miller_name"]
                    + " ("
                    + df_mil_available["milling_date"]
                    + ")"
                )
                
                default_mil_idx = 0
                if st.session_state["edit_fg_id"] is not None and edit_fg_data is not None:
                    matched_mil = df_mil_available[df_mil_available["id"] == edit_fg_data["milling_id"]]
                    if not matched_mil.empty:
                        matched_label = matched_mil.iloc[0]["label"]
                        if matched_label in df_mil_available["label"].tolist():
                            default_mil_idx = df_mil_available["label"].tolist().index(matched_label)

                sel_milling = st.selectbox(
                    "Select Milling Batch", df_mil_available["label"].tolist(), index=default_mil_idx, key="sel_milling_fg"
                )
                
                if sel_milling is not None:
                    row_mil = df_mil_available[df_mil_available["label"] == sel_milling].iloc[0]
                    milling_id = int(row_mil["id"])
                    miller_name = row_mil["miller_name"]
                    milling_qty = float(row_mil["milling_qty"])
                    milling_date_str = row_mil["milling_date"]

                    st.info(f"Selected Miller: **{miller_name}** | Milling Date: **{milling_date_str}** | Milling Qty: **{milling_qty:,.2f} kg**")

                    with st.form("fg_form", clear_on_submit=False):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            default_prod_date = datetime.date.today()
                            if edit_fg_data is not None:
                                try:
                                    default_prod_date = datetime.datetime.strptime(edit_fg_data["production_date"], "%d %b %Y").date()
                                except Exception:
                                    pass
                            prod_date_obj = st.date_input("Production Date", value=default_prod_date)
                            production_date = prod_date_obj.strftime("%d %b %Y")
                        with c2:
                            default_mfd = datetime.date.today()
                            if edit_fg_data is not None:
                                try:
                                    default_mfd = datetime.datetime.strptime("01 " + edit_fg_data["mfd_date"], "%d %b %Y").date()
                                except Exception:
                                    pass
                            mfd_date_obj = st.date_input("MFD Date", value=default_mfd)
                            mfd_date = mfd_date_obj.strftime("%b %Y")
                        with c3:
                            default_exp = datetime.date.today() + datetime.timedelta(days=180)
                            if edit_fg_data is not None:
                                try:
                                    default_exp = datetime.datetime.strptime(edit_fg_data["expiry_date"], "%d %b %Y").date()
                                except Exception:
                                    pass
                            expiry_date_obj = st.date_input("Expiry Date", value=default_exp)
                            expiry_date = expiry_date_obj.strftime("%d %b %Y")

                        st.divider()
                        st.subheader("SKU & MRP Configuration")
                        
                        sku_options = ["500g Pouch", "1kg Pouch", "2kg Pouch", "5kg Pouch", "Custom SKU"]
                        default_sku_idx = 0
                        if edit_fg_data is not None:
                            p_code = edit_fg_data["product_code"]
                            if "500g" in p_code: default_sku_idx = 0
                            elif "1kg" in p_code: default_sku_idx = 1
                            elif "2kg" in p_code: default_sku_idx = 2
                            elif "5kg" in p_code: default_sku_idx = 3
                            else: default_sku_idx = 4

                        sc1, sc2, sc3, sc4 = st.columns(4)
                        with sc1:
                            sku_type = st.selectbox("Select SKU Type", sku_options, index=default_sku_idx, key="fg_sku_type")
                        with sc2:
                            default_pcode = edit_fg_data["product_code"] if edit_fg_data is not None else "BN-ATTA-1KG"
                            product_code = st.text_input("Product Code / SKU Name", value=default_pcode)
                        with sc3:
                            default_mrp = float(edit_fg_data["mrp"]) if edit_fg_data is not None else 0.0
                            mrp = st.number_input("MRP (Rs)", value=default_mrp, step=1.0, format="%.2f")
                        with sc4:
                            default_p_count = 0
                            if edit_fg_data is not None:
                                default_p_count = int(edit_fg_data.get("pouch_1kg", 0) or edit_fg_data.get("pouch_500g", 0) or edit_fg_data.get("pouch_2kg", 0) or edit_fg_data.get("pouch_5kg", 0))
                            pouch_count = st.number_input("Number of Pouches / Units", min_value=0, value=default_p_count, step=1)

                        st.divider()
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            default_bran = float(edit_fg_data["bran_qty"]) if edit_fg_data is not None else 0.0
                            bran_qty = st.number_input("Bran Quantity (kg)", min_value=0.0, value=default_bran, step=1.0, format="%.2f")
                        with rc2:
                            default_refr = float(edit_fg_data["refraction_qty"]) if edit_fg_data is not None else 0.0
                            refraction_qty = st.number_input("Refraction Quantity (kg)", min_value=0.0, value=default_refr, step=1.0, format="%.2f")

                        btn_label_fg = "Update Finished Goods" if st.session_state["edit_fg_id"] is not None else "Calculate Yield & Save Finished Goods"
                        submit_fg = st.form_submit_button(label=btn_label_fg)

                        if submit_fg:
                            f_mrp = float(mrp) if mrp is not None else 0.0
                            f_bran = float(bran_qty) if bran_qty is not None else 0.0
                            f_refr = float(refraction_qty) if refraction_qty is not None else 0.0
                            f_count = int(pouch_count) if pouch_count is not None else 0

                            multiplier = 1.0
                            if "500g" in sku_type:
                                multiplier = 0.5
                            elif "1kg" in sku_type:
                                multiplier = 1.0
                            elif "2kg" in sku_type:
                                multiplier = 2.0
                            elif "5kg" in sku_type:
                                multiplier = 5.0
                            else:
                                multiplier = 1.0

                            total_finished_qty = f_count * multiplier

                            bran_pct = (f_bran / milling_qty) * 100 if milling_qty > 0 else 0.0
                            refraction_pct = (f_refr / milling_qty) * 100 if milling_qty > 0 else 0.0
                            yield_pct = (total_finished_qty / milling_qty) * 100 if milling_qty > 0 else 0.0

                            total_accounted = total_finished_qty + f_bran + f_refr
                            processing_loss_qty = milling_qty - total_accounted
                            processing_loss_pct = (processing_loss_qty / milling_qty) * 100 if milling_qty > 0 else 0.0

                            conn = get_connection()
                            cursor = conn.cursor()

                            if st.session_state["edit_fg_id"] is not None:
                                cursor.execute(
                                    """
                                    UPDATE finished_goods 
                                    SET milling_id=?, production_date=?, miller_name=?, mfd_date=?, expiry_date=?, mrp=?, product_code=?, pouch_500g=?, pouch_1kg=?, pouch_2kg=?, pouch_5kg=?, total_finished_qty=?, bran_qty=?, bran_pct=?, refraction_qty=?, refraction_pct=?, yield_pct=?, processing_loss_pct=?
                                    WHERE id=?
                                """,
                                    (
                                        milling_id,
                                        production_date,
                                        miller_name,
                                        mfd_date,
                                        expiry_date,
                                        f_mrp,
                                        product_code,
                                        f_count if "500g" in sku_type else 0,
                                        f_count if "1kg" in sku_type else 0,
                                        f_count if "2kg" in sku_type else 0,
                                        f_count if "5kg" in sku_type else 0,
                                        round(total_finished_qty, 2),
                                        f_bran,
                                        f"{bran_pct:.2f}%",
                                        f_refr,
                                        f"{refraction_pct:.2f}%",
                                        f"{yield_pct:.2f}%",
                                        f"{processing_loss_pct:.2f}%",
                                        st.session_state["edit_fg_id"],
                                    ),
                                )
                                conn.commit()
                                conn.close()
                                st.success(f"Finished Goods Record ID {st.session_state['edit_fg_id']} Updated Successfully!")
                                st.session_state["edit_fg_id"] = None
                                st.rerun()
                            else:
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
                                        f_mrp,
                                        product_code,
                                        f_count if "500g" in sku_type else 0,
                                        f_count if "1kg" in sku_type else 0,
                                        f_count if "2kg" in sku_type else 0,
                                        f_count if "5kg" in sku_type else 0,
                                        round(total_finished_qty, 2),
                                        f_bran,
                                        f"{bran_pct:.2f}%",
                                        f_refr,
                                        f"{refraction_pct:.2f}%",
                                        f"{yield_pct:.2f}%",
                                        f"{processing_loss_pct:.2f}%",
                                    ),
                                )
                                conn.commit()
                                conn.close()
                                st.success(
                                    f"Finished Goods Saved! SKU: {sku_type} | Qty: {total_finished_qty:,.2f} kg | MRP: Rs {f_mrp:.2f}"
                                )
                                st.rerun()

    st.subheader("Saved Finished Goods Records")
    df_fg_saved_show = load_data("finished_goods")
    if not df_fg_saved_show.empty:
        st.dataframe(df_fg_saved_show, use_container_width=True)
