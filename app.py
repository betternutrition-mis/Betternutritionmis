invoice_number = st.text_input("Invoice Number *")

with rc3:
      gross_qty = st.number_input("Gross Qty", min_value=0.0, step=50.0)
      gross_qty = st.number_input(
          "Gross Qty *", value=None, step=50.0, placeholder="Type..."
      )
bag_type = st.selectbox("Bag Type", ["Jute Bag", "Plastic Bag"])
      total_bags = st.number_input("Number Of Total Bags", min_value=0, step=10)
      bag_wt = st.number_input("Bag Wt", min_value=0.0, step=0.1)

    net_wt = gross_qty - (total_bags * bag_wt)
    st.info(
        f"Calculated Net Wt (Gross Qty - [Total Bags * Bag Wt]):"
        f" **{net_wt:,.2f}**"
    )

    # Mandatory Validation Condition
    is_valid_rm = bool(vendor_name.strip()) and bool(material_name.strip()) and bool(vehicle_number.strip()) and bool(po_number.strip()) and bool(invoice_number.strip()) and (gross_qty > 0) and (total_bags > 0) and (bag_wt > 0)

    submit_rm = st.form_submit_button(
        label="Save Raw Material Entry", disabled=not is_valid_rm
    )

    if not is_valid_rm:
      st.warning(
          "⚠️ कृपया सभी अनिवार्य फील्ड्स (Vendor, Material, Vehicle, PO,"
          " Invoice, Qty, Bags) भरें, तभी सेव बटन चालू होगा।"
      total_bags = st.number_input(
          "Number Of Total Bags *", value=None, step=10, placeholder="Type..."
      )
      bag_wt = st.number_input(
          "Bag Wt *", value=None, step=0.1, placeholder="Type..."
)

    if submit_rm and is_valid_rm:
      data = {
          "entry_date": entry_date,
          "vendor_name": vendor_name.strip(),
          "material_name": material_name.strip(),
          "miller_name": miller_name,
          "vehicle_number": vehicle_number.strip(),
          "po_number": po_number.strip(),
          "invoice_number": invoice_number.strip(),
          "gross_qty": float(gross_qty),
          "bag_type": bag_type,
          "total_bags": int(total_bags),
          "bag_wt": float(bag_wt),
          "net_wt": round(float(net_wt), 2),
          "entered_by": current_logged_user,
      }
      supabase.table("raw_material").insert(data).execute()
      st.success("Raw Material Entry Saved Successfully!")
      st.rerun()
    # Calculate net weight safely if inputs are provided
    if (
        gross_qty is not None
        and total_bags is not None
        and bag_wt is not None
    ):
      net_wt = gross_qty - (total_bags * bag_wt)
      st.info(
          f"Calculated Net Wt (Gross Qty - [Total Bags * Bag Wt]):"
          f" **{net_wt:,.2f}**"
      )
    else:
      net_wt = 0.0

    submit_rm = st.form_submit_button(label="Save Raw Material Entry")

    if submit_rm:
      if (
          not vendor_name.strip()
          or not material_name.strip()
          or not vehicle_number.strip()
          or not po_number.strip()
          or not invoice_number.strip()
          or gross_qty is None
          or total_bags is None
          or bag_wt is None
      ):
        st.error("⚠️ कृपया सभी अनिवार्य (Mandatory) फील्ड्स सही से भरें!")
      else:
        data = {
            "entry_date": entry_date,
            "vendor_name": vendor_name.strip(),
            "material_name": material_name.strip(),
            "miller_name": miller_name,
            "vehicle_number": vehicle_number.strip(),
            "po_number": po_number.strip(),
            "invoice_number": invoice_number.strip(),
            "gross_qty": float(gross_qty),
            "bag_type": bag_type,
            "total_bags": int(total_bags),
            "bag_wt": float(bag_wt),
            "net_wt": round(float(net_wt), 2),
            "entered_by": current_logged_user,
        }
        supabase.table("raw_material").insert(data).execute()
        st.success("Raw Material Entry Saved Successfully!")
        st.rerun()

st.divider()
st.subheader("Saved Raw Material Records")
@@ -259,42 +274,54 @@ def get_miller_input(key_prefix, default_val=None):

qc1, qc2 = st.columns(2)
with qc1:
        hl = st.number_input("HL (Hectolitre Weight)", min_value=0.0, step=0.1)
        hl = st.number_input(
            "HL (Hectolitre Weight) *",
            value=None,
            step=0.1,
            placeholder="Type...",
        )
foreign_material = st.number_input(
            "Foreign Material %", min_value=0.0, step=0.01, format="%.2f"
            "Foreign Material % *",
            value=None,
            step=0.01,
            format="%.2f",
            placeholder="Type...",
)

with qc2:
moisture = st.number_input(
            "Moisture %", min_value=0.0, step=0.1, format="%.1f"
            "Moisture % *",
            value=None,
            step=0.1,
            format="%.1f",
            placeholder="Type...",
)
visibility = st.text_input(
"Visibility / Grain Appearance *", placeholder="e.g. Clean / Clear"
)

      is_valid_q = bool(visibility.strip()) and (hl > 0) and (moisture > 0)

      submit_q = st.form_submit_button(
          label="Save Quality Entry", disabled=not is_valid_q
      )
      submit_q = st.form_submit_button(label="Save Quality Entry")

      if not is_valid_q:
        st.warning(
            "⚠️ कृपया सभी क्वालिटी पैरामीटर और Visibility सही से भरें।"
        )

      if submit_q and is_valid_q:
        data = {
            "invoice_number": invoice_number,
            "hl": float(hl),
            "foreign_material": float(foreign_material),
            "moisture": float(moisture),
            "visibility": visibility.strip(),
            "entered_by": current_logged_user,
        }
        supabase.table("raw_material_quality").insert(data).execute()
        st.success("Quality Entry Saved Successfully!")
        st.rerun()
      if submit_q:
        if (
            hl is None
            or foreign_material is None
            or moisture is None
            or not visibility.strip()
        ):
          st.error("⚠️ कृपया सभी क्वालिटी पैरामीटर भरना अनिवार्य है!")
        else:
          data = {
              "invoice_number": invoice_number,
              "hl": float(hl),
              "foreign_material": float(foreign_material),
              "moisture": float(moisture),
              "visibility": visibility.strip(),
              "entered_by": current_logged_user,
          }
          supabase.table("raw_material_quality").insert(data).execute()
          st.success("Quality Entry Saved Successfully!")
          st.rerun()

st.divider()
st.subheader("Saved Raw Material Quality Records")
@@ -323,7 +350,9 @@ def get_miller_input(key_prefix, default_val=None):
with mc1:
mil_date_obj = st.date_input("Date", value=datetime.date.today())
milling_date = mil_date_obj.strftime("%d %b %Y")
      milling_qty = st.number_input("QTY (kg)", min_value=0.0, step=50.0)
      milling_qty = st.number_input(
          "QTY (kg) *", value=None, step=50.0, placeholder="Type..."
      )

with mc2:
material_type = st.text_input(
@@ -333,33 +362,27 @@ def get_miller_input(key_prefix, default_val=None):
"Batch Code of Milling *", placeholder="e.g. MILL-BATCH-01"
)

    is_valid_mill = (
        bool(material_type.strip())
        and bool(batch_code.strip())
        and (milling_qty > 0)
    )

    submit_milling = st.form_submit_button(
        label="Save Milling Entry", disabled=not is_valid_mill
    )
    submit_milling = st.form_submit_button(label="Save Milling Entry")

    if not is_valid_mill:
      st.warning(
          "⚠️ कृपया Material Type, Batch Code और Qty पूरी तरह भरें।"
      )

    if submit_milling and is_valid_mill:
      data = {
          "milling_date": milling_date,
          "miller_name": miller,
          "milling_qty": float(milling_qty),
          "material_type": material_type.strip(),
          "batch_code": batch_code.strip(),
          "entered_by": current_logged_user,
      }
      supabase.table("milling").insert(data).execute()
      st.success("Milling Entry Saved Successfully!")
      st.rerun()
    if submit_milling:
      if (
          not material_type.strip()
          or not batch_code.strip()
          or milling_qty is None
      ):
        st.error("⚠️ कृपया Material Type, Batch Code और Qty सही से भरें!")
      else:
        data = {
            "milling_date": milling_date,
            "miller_name": miller,
            "milling_qty": float(milling_qty),
            "material_type": material_type.strip(),
            "batch_code": batch_code.strip(),
            "entered_by": current_logged_user,
        }
        supabase.table("milling").insert(data).execute()
        st.success("Milling Entry Saved Successfully!")
        st.rerun()

st.divider()
st.subheader("Saved Milling Records")
@@ -399,40 +422,40 @@ def get_miller_input(key_prefix, default_val=None):
use_by_date = use_obj.strftime("%d %b %Y")

with fc2:
      mrp = st.number_input("MRP", min_value=0.0, step=1.0)
      mrp = st.number_input(
          "MRP *", value=None, step=1.0, placeholder="Type..."
      )
batch_number = st.text_input("Batch Number *")
      qty = st.number_input("Quantity (Packets)", min_value=0, step=10)
      qty = st.number_input(
          "Quantity (Packets) *", value=None, step=10, placeholder="Type..."
      )

with fc3:
drop_test = st.selectbox("Drop Test Status", ["Pass", "Fail"])
sealing = st.selectbox("Sealing Quality", ["Good", "Average", "Bad"])

    is_valid_fg = bool(batch_number.strip()) and (mrp > 0) and (qty > 0)

    submit_fg = st.form_submit_button(
        label="Save Finished Goods Entry", disabled=not is_valid_fg
    )
    submit_fg = st.form_submit_button(label="Save Finished Goods Entry")

    if not is_valid_fg:
      st.warning("⚠️ कृपया Batch Number, MRP और Quantity सही से भरें।")

    if submit_fg and is_valid_fg:
      data = {
          "production_date": production_date,
          "miller_name": miller_name,
          "sku": sku,
          "mfd_date": mfd_date,
          "use_by_date": use_by_date,
          "mrp": float(mrp),
          "batch_number": batch_number.strip(),
          "qty": int(qty),
          "drop_test": drop_test,
          "sealing": sealing,
          "entered_by": current_logged_user,
      }
      supabase.table("finished_goods").insert(data).execute()
      st.success("Finished Goods Entry Saved Successfully!")
      st.rerun()
    if submit_fg:
      if mrp is None or not batch_number.strip() or qty is None:
        st.error("⚠️ कृपया MRP, Batch Number और Quantity सही से भरें!")
      else:
        data = {
            "production_date": production_date,
            "miller_name": miller_name,
            "sku": sku,
            "mfd_date": mfd_date,
            "use_by_date": use_by_date,
            "mrp": float(mrp),
            "batch_number": batch_number.strip(),
            "qty": int(qty),
            "drop_test": drop_test,
            "sealing": sealing,
            "entered_by": current_logged_user,
        }
        supabase.table("finished_goods").insert(data).execute()
        st.success("Finished Goods Entry Saved Successfully!")
        st.rerun()

st.divider()
st.subheader("Saved Finished Goods Inventory")
@@ -509,23 +532,19 @@ def get_miller_input(key_prefix, default_val=None):
new_pin = st.text_input("4-Digit PIN *", type="password")
new_role = st.selectbox("Role", ["Admin", "Team"])

      is_valid_emp = bool(new_emp_name.strip()) and bool(new_pin.strip())

      sub_emp = st.form_submit_button(
          "Create Employee", disabled=not is_valid_emp
      )

      if not is_valid_emp:
        st.warning("⚠️ कृपया Employee Name और 4-Digit PIN दोनों भरें।")
      sub_emp = st.form_submit_button("Create Employee")

      if sub_emp and is_valid_emp:
        data = {
            "employee_name": new_emp_name.strip(),
            "pin": new_pin.strip(),
            "role": new_role,
        }
        supabase.table("employees").insert(data).execute()
        st.success("Employee added successfully!")
        st.rerun()
      if sub_emp:
        if not new_emp_name.strip() or not new_pin.strip():
          st.error("⚠️ कृपया Employee Name और 4-Digit PIN दोनों भरें।")
        else:
          data = {
              "employee_name": new_emp_name.strip(),
              "pin": new_pin.strip(),
              "role": new_role,
          }
          supabase.table("employees").insert(data).execute()
          st.success("Employee added successfully!")
          st.rerun()
else:
st.info("🔒 Admin actions are restricted to Admin role users only.")
