from flask import Flask, request, render_template
import functions

app = Flask(__name__)

@app.route('/')
def render_static():
    return render_template('GetOut.html')

@app.route('/user_location')
def get_location():
    location_dict = {'City': '', 'State': ''}
    city = request.args.get("city")
    location_dict['City'] = city.replace(" ","_")
    state = request.args.get("state")
    location_dict['State'] = state.replace(" ","_")
    recommendation = functions.send_to_bit(location_dict)
    return render_template("%s.html" %recommendation)

if __name__ == "__main__":
    app.run(debug=True)