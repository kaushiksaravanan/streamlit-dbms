import streamlit as st
from pymongo.mongo_client import MongoClient
import mysql.connector as ms
import random

food_pic = {'Dosa': 'https://pipingpotcurry.com/wp-content/uploads/2020/11/Dosa-recipe-plain-sada-dosa-Piping-Pot-Curry-1159x1536.webp',
            'Idly': 'https://www.vegrecipesofindia.com/wp-content/uploads/2021/06/idli-recipe-1.jpg',
            'Parota': 'https://www.chitrasfoodbook.com/ezoimgfmt/farm9.staticflickr.com/8586/16023214373_90552b64f6_o.jpg?ezimgfmt=ng%3Awebp%2Fngcb1%2Frs%3Adevice%2Frscb1-1'}
# Goto C:\Users\Kau\.streamlit and create confi.toml

# client = MongoClient(host="localhost", port=27017)
client = MongoClient(
    "mongodb+srv://admin:admin@cluster0.max1z.mongodb.net/?retryWrites=true&w=majority")
db = client['Dbms']

conn = ms.connect(host="sql6.freemysqlhosting.net", user="sql6497487",
                  password="X85HAWMFMi", database="sql6497487")
cur = conn.cursor()

username = None


def get(food_name):
    food_name = food_name.lower()
    foods = db.Foods
    quer = {"food_name": food_name}
    url = foods.find_one(quer)

    if url is not None:
        return url['url']
    else:
        return 0


def username_unique(username):
    Users = db.Users
    req_doc = Users.find_one({"c_id": f"{username}"})
    # unq = True
    # query = f"SELECT f_name FROM customer WHERE c_id = '{username}'"
    # cur = conn.cursor(buffered=True)
    # cur.execute(query)
    # row = cur.fetchone()
    # cur.close()
    # if row is None:
    #     print("Unique")
    #     unq = True
    # else:
    #     unq = False
    return (req_doc is None)


def authenticate(username, password):
    authenticated = True
    Users = db.Users
    req_doc = Users.find_one({"c_id": f"{username}"})
    print(req_doc)
    if req_doc is not None:
        authenticated = (password == req_doc['pwd'])
    else:
        authenticated = False
    # query = f"SELECT pwd FROM customer WHERE c_id = '{username}'"
    # cur = conn.cursor(buffered=True)
    # cur.execute(query)

    # pwd = None
    # for [pwd] in cur:
    #     print(pwd)
    # if pwd is None:
    #     print("Username doesn't exist")
    #     authenticated = False
    # else:
    #     if pwd == password:
    #         authenticated = True
    #     else:
    #         authenticated = False

    return authenticated


def savedetails(username, F_name, L_name, Location, password):
    Users = db.Users
    insertDoc = {
        "c_id": f"{username}", "dp_id": None,
        "c_location": f"{Location}",
        "f_name": f"{F_name}",
        "l_name": f"{L_name}",
        "pwd": f"{password}"
    }
    try:
        res = Users.insert_one(insertDoc)
        print(res)
        return True
    except Exception as e:
        print(e)
        return False
    # query = f"INSERT INTO customer (C_id, f_name, l_name, c_location, pwd) VALUES ('{username}','{F_name}','{L_name}','{Location}','{password}')"
    # cur = conn.cursor()
    # cur.execute(query)
    # conn.commit()
    # return True


def get_hotels():
    query = "SELECT h_id, h_name FROM hotel"
    a = conn.cursor(buffered=True)
    with a:
        a.execute(query)
        retrieved = a.fetchall()
    return retrieved


def get_food(hotelId):
    query = f"SELECT f_name, f_id, f_price FROM food A WHERE f_id IN (SELECT f_id FROM serves B WHERE B.h_id = '{hotelId}')"
    a = conn.cursor(buffered=True)
    foodInfo = None
    with a:
        a.execute(query)
        foodInfo = a.fetchall()
    # list(map(lambda x: ))
    print(len(foodInfo), hotelId)
    if len(foodInfo) != 0:
        return foodInfo
    else:
        return [('Parota', "C", 40)]


def selectedDP():
    # Randomly selects a delivery person who will be delivering the food.
    query = "SELECT dp_id, f_name, l_name FROM delivery_person"
    with conn.cursor(buffered=True) as a:
        a.execute(query)
        b = a.fetchall()

    return b[random.randint(0, len(b) - 1)]


def place_order(order, Total, hotelId):
    #update in table
    orderPlaced = True, None
    # Randomly selects a delivery person for the order
    delPerId, del_FName, del_Lname = selectedDP()
    query1 = f"INSERT INTO orders(h_id, dp_id, o_total_price) VALUES('{hotelId}', '{delPerId}', {Total})"
    # query2 = f"UPDATE customer  SET dp_id = '{delPerId}' WHERE c_id = '{username}'"  # Settings the delivery person who will delivery the customer his/her current delivery.
    Users = db.Users

    try:
        with conn.cursor() as a:
            a.execute(query1)
            # a.execute(query2)
            conn.commit()
        Users.update_one({"c_id": f"{username}"}, {
                         "$set": {"dp_id": f"{delPerId}"}})
        orderPlaced = (True, del_FName + " " + del_Lname)
    except Exception as e:
        print(e)
        orderPlaced = False, None

    return orderPlaced


def show_food(hotelId, hotel, Location):
    foods = get_food(hotelId)
    food_ = [i[0] for i in foods]
    food_i = [i[1] for i in foods]
    price = [i[2] for i in foods]
    food_ = st.columns(len(food_))
    k = 0
    Total = 0
    order = {}
    for i in food_:
        with i:
            st.header(foods[k][0])
            # st.checkbox(foods[k][0],key=food_i[k])
            str_temp = 'Price ₹'+str(price[k])
            st.write(str_temp)
            no = st.number_input('Quantity', 0, 100,
                                 key=(k*food_i))  # type: ignore
            Total += (no*price[k])
            order[food_i[k]] = no
            st.image(get(foods[k][0]))
            k += 1
    str_total = '# Total '+str(int(Total))
    st.write(str_total)
    str_location = '## Your delivery address - '+Location
    st.write(str_location)
    st.write("Order once placed can't be refunded")
    y = st.button('Place Order')

    # FOr backend order is a dict of order,quantity
    st.write(order)
    if y:
        res = place_order(order, Total, hotelId)
        if res[0] == True:
            st.success(f'Order placed 🤩. Delivery Agent: {res[1]}')
        else:
            st.error('Order Failed 😔')
    else:
        st.write('Avaialabe payment method Cash on delivery')


def create():
    list_hotels = get_hotels()
    hotel_names = list(map(lambda x: x[1], list_hotels))
    st.write('# Choose Hotel')
    selHotel = st.radio('Currently open hotels', hotel_names)  # Select a hotel
    selHotelId = list_hotels[hotel_names.index(selHotel)][0]

    query = f"SELECT h_location FROM hotel WHERE h_id = '{selHotelId}'"
    location = None
    curr = conn.cursor(buffered=True)
    with curr:
        curr.execute(query)
        record = curr.fetchone()
        location = record[0]

    show_food(selHotelId, selHotel, location)


def login(username):
    if len(username) > 0:
        login_cfrm = 'Logged in as '+username
        st.success(login_cfrm)
        # get user's location' as parameted to create
        create()

# with s/.expander('LOGIN'):


def main():
    global username
    username = st.text_input('Username')
    password = st.text_input('Password', type="password")
    b = st.button('Login')

    # SELECT pwd from username
    pwd = ''
    if authenticate(username, password):
        login(username)
    elif b:
        st.error('Wrong credentials')
    with st.sidebar:
        if st.checkbox('REGISTER'):
            with st.form(key='LOGIN'):
                # Cid = Username
                username = st.text_input('Type Username')
                # if len(username)>0:
                F_name = st.text_input('First name')
                L_name = st.text_input('Last name')
                Location = st.text_input('Location')
                Password = st.text_input('Password', type="password")
                y = st.form_submit_button('Register')
                if not username_unique(username) and y:
                    print('1')
                    st.error('Username already exists')
                elif y:
                    print(2)
                    st.info('Username avaliable')
                    if savedetails(username, F_name, L_name, Location, Password):
                        st.success('Successfully registed')
                    else:
                        st.error("Can't complete registration contact dev team")


if __name__ == '__main__':
    main()
