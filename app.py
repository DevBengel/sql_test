from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import qrcode
import qrcode.image.svg
import io
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Secret key configuration
app.secret_key = os.getenv('SECRET_KEY')

# App Settings
app.config['threaded'] = True

# Database configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# Initialize MySQL
mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM urls")
    urls = cursor.fetchall()
    return render_template('index.html', urls=urls)

@app.route('/urls/<int:id>')
def url_details(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM urls WHERE id = %s", (id,))
    url = cursor.fetchone()
    qr_svg_url1 = url_for('qr_code', url=url['url1'])
    qr_svg_url2 = url_for('qr_code', url=url['url2'])
    return render_template('url_details.html', url=url, qr_svg_url1=qr_svg_url1, qr_svg_url2=qr_svg_url2)

@app.route('/create_url', methods=['GET', 'POST'])
def create_url():
    if request.method == 'POST':
        url1 = request.form['url1']
        url1_reachable = request.form['url1_reachable'] == 'true'
        url2 = request.form['url2']
        url2_reachable = request.form['url2_reachable'] == 'true'
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO urls (url1, url1_reachable, url2, url2_reachable) VALUES (%s, %s, %s, %s)", 
                       (url1, url1_reachable, url2, url2_reachable))
        mysql.connection.commit()
        return redirect(url_for('index'))
    return render_template('create_url.html')

@app.route('/update_url/<int:id>', methods=['GET', 'POST'])
def update_url(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM urls WHERE id = %s", (id,))
    url = cursor.fetchone()
    
    if request.method == 'POST':
        url1 = request.form['url1']
        url1_reachable = request.form['url1_reachable'] == 'true'
        url2 = request.form['url2']
        url2_reachable = request.form['url2_reachable'] == 'true'
        
        cursor.execute("""
            UPDATE urls 
            SET url1 = %s, url1_reachable = %s, url2 = %s, url2_reachable = %s 
            WHERE id = %s
        """, (url1, url1_reachable, url2, url2_reachable, id))
        mysql.connection.commit()
        return redirect(url_for('index'))
    return render_template('update_url.html', url=url)

@app.route('/delete_url/<int:id>', methods=['POST'])
def delete_url(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM urls WHERE id = %s", (id,))
    mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/qr_code/<path:url>')
def qr_code(url):
    qr_svg = generate_qr_code_svg(url)
    return send_file(io.BytesIO(qr_svg.encode('utf-8')), mimetype='image/svg+xml', as_attachment=False, download_name='qrcode.svg')

def generate_qr_code_svg(url):
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        image_factory=factory
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue().decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)
