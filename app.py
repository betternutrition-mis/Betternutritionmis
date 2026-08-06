if action_type_fg == "➕ New Finished Goods Entry" or st.session_state["edit_fg_id"] is not None:
            
            # --- Ye filtering add karni hai taaki duplicate batches na dikhein ---
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
