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
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.warning(
                    "Database file delete ho chuki hai. App ko refresh karein"
                    " naye tables banane ke liye."
                )
                st.rerun()
            else:
                st.error("Database file nahi mili.")
