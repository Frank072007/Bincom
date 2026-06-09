from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-335a5660-chinedueke2007-c30d.e.aivencloud.com",
        port="25702", # Usually 25060 for Aiven
        user="avnadmin",
        password="AVNS__3Tym9xTgqK6M4hu3an",
        database="defaultdb" # Aiven usually names the default database "defaultdb"
    )

@app.route('/q1', methods=['GET', 'POST'])
def pu_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT uniqueid, polling_unit_name, polling_unit_number FROM polling_unit WHERE polling_unit_name IS NOT NULL")
    polling_units = cursor.fetchall()

    results = None

    if request.method == 'POST':
        pu_id = request.form.get('pu_id')
        cursor.execute("SELECT party_abbreviation, party_score FROM announced_pu_results WHERE polling_unit_uniqueid = %s", (pu_id,))
        results = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('q1.html', polling_units=polling_units, results=results)

@app.route('/q2', methods=['GET', 'POST'])
def lga_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT lga_id, lga_name FROM lga")
    lgas = cursor.fetchall()

    results = None

    if request.method == 'POST':
        lga_id = request.form.get('lga_id')

        query = """
            SELECT pu_res.party_abbreviation, SUM(pu_res.party_score) as total_score
            FROM announced_pu_results pu_res
            JOIN polling_unit pu ON pu_res.polling_unit_uniqueid = pu.uniqueid
            WHERE pu.lga_id = %s
            GROUP BY pu_res.party_abbreviation
        """
        cursor.execute(query, (lga_id,))
        results = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('q2.html', lgas=lgas, results=results)

@app.route('/q3', methods=['GET', 'POST'])
def add_results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        pu_id = request.form.get('pu_id')
        entered_by = request.form.get('entered_by')
        ip_address = request.remote_addr
        date_entered = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        parties = ['PDP', 'DPP', 'ACN', 'PPA', 'CDC', 'JP', 'ANPP', 'LABO', 'CPP']
        
        for party in parties:
            score = request.form.get(party)
            if score and score.isdigit():
                insert_query = """
                    INSERT INTO announced_pu_results
                    (polling_unit_uniqueid, party_abbreviation, party_score, entered_by_user, date_entered, user_ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (pu_id, party, score, entered_by, date_entered, ip_address))

        conn.commit()
        flash("Results successfully saved to the database!")
        return redirect(url_for('add_results'))

    cursor.execute("SELECT lga_id, lga_name FROM lga")
    lgas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('q3.html', lgas=lgas)

@app.route('/api/wards/<int:lga_id>')
def get_wards(lga_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ward_id, ward_name FROM ward WHERE lga_id = %s", (lga_id,))
    wards = cursor.fetchall()
    conn.close()
    return jsonify(wards)

@app.route('/api/polling_units/<int:ward_id>')
def get_polling_units(ward_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT uniqueid, polling_unit_name FROM polling_unit WHERE ward_id = %s", (ward_id,))
    units = cursor.fetchall()
    conn.close()
    return jsonify(units)

if __name__ == '__main__':
    app.run(debug=True)