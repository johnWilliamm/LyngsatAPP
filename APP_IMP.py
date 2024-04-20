

import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd  # Importing pandas for DataFrame handling
import os 

def create_connection():
    """Establish a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host='mysql-lyngsatdatabase.alwaysdata.net',
            database='lyngsatdatabase_1',
            user='356412',
            password='*M>6}B8WMv#:]zJ',
            ssl_disabled=False
        )
        return connection
    except Error as e:
        st.error(f"Database connection failed: {e}")
        return None

def register_user(name, email, gender, birthdate, address, region):
    """Register a new user in the sysuser table."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO sysuser (user_name, user_email, Gender, Birthdate, Address, Region) 
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (name, email, gender, birthdate, address, region))
            connection.commit()
            st.success("User registered successfully!")
        except Error as e:
            st.error(f"Failed to register user: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def create_favorites_list(email, favorite_channel_id):
    """Create a favorite channel entry for a specific user."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO userfavchannel (user_email, channel_id) VALUES (%s, %s);"
            cursor.execute(query, (email, favorite_channel_id))
            connection.commit()
            st.success(f"Favorite channel added for email {email}.")
        except Error as e:
            st.error(f"Failed to add favorite channel: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def list_viewable_channels(longitude):
    """List all channels viewable from a certain longitude."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT SC.channel_name, S.satellite_name, S.position
            FROM syschannels SC
            JOIN satellites S ON SC.satellite_name = S.satellite_name
            WHERE S.position BETWEEN %s AND %s;
            """
            lower_bound = longitude - 10
            upper_bound = longitude + 10
            cursor.execute(query, (lower_bound, upper_bound))
            results = cursor.fetchall()
            return results
        except Error as e:
            st.error(f"Error: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def show_user_favorite_channels(email, longitude):
    """Show favorite channels for a user based on location."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT UC.user_email, SC.channel_name, SC.freq, S.satellite_name, SC.channel_encryption
            FROM userfavchannel UC
            JOIN syschannels SC ON UC.channel_id = SC.channel_id
            JOIN satellites S ON SC.satellite_name = S.satellite_name
            WHERE UC.user_email = %s AND S.position BETWEEN %s AND %s;
            """
            lower_bound = longitude - 10
            upper_bound = longitude + 10
            cursor.execute(query, (email, lower_bound, upper_bound))
            results = cursor.fetchall()
            return results
        except Error as e:
            st.error(f"Error: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def top_five_providers():
    """Show the top 5 TV Networks / Providers by number of channels and the average number of satellites each channel is available on."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT provider_name, COUNT(*) AS channel_count, AVG(num_satellites) AS avg_satellites_per_channel
            FROM (
                SELECT p.provider_name, c.channel_name, COUNT(DISTINCT c.satellite_name) AS num_satellites
                FROM sysprovider p
                JOIN syschannels c ON p.channel_name = c.channel_name
                WHERE p.provider_name IS NOT NULL AND p.provider_name <> ''
                GROUP BY p.provider_name, c.channel_name
            ) AS subquery
            GROUP BY provider_name
            ORDER BY channel_count DESC
            LIMIT 5;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            print("Top 5 TV Networks / Providers:")
            return results
        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def top_five_rockets():
    """Show the top 5 rockets in terms of the number of satellites they put in orbit."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT launch_rocket, COUNT(*) AS num_satellites
            FROM satellites
            GROUP BY launch_rocket
            ORDER BY num_satellites DESC
            LIMIT 5;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            print("Top 5 Rockets by Satellites Launched:")
            return results
        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def top_growing_satellites():
    """Show the top 5 growing satellites using the number of channels they host compared to their launch date."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT S.satellite_name, COUNT(*) AS channel_count, DATEDIFF(CURDATE(), S.launch_date) AS days_since_launch,
                (COUNT(*) / DATEDIFF(CURDATE(), S.launch_date)) AS growth_rate
            FROM syschannels SC
            JOIN satellites S ON SC.satellite_name = S.satellite_name
            GROUP BY S.satellite_name
            ORDER BY growth_rate DESC
            LIMIT 5;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            print("Top 5 Growing Satellites:")
            return results
        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def top_channels_by_language():
    """Show the top 5 channels for each language by the number of satellites they are hosted on."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            WITH ChannelRankings AS (
                SELECT 
                    channel_language, 
                    channel_name, 
                    COUNT(DISTINCT satellite_name) AS satellite_count,
                    ROW_NUMBER() OVER (PARTITION BY channel_language ORDER BY COUNT(DISTINCT satellite_name) DESC) AS ranking
                FROM syschannels
                WHERE channel_language IS NOT NULL AND channel_language <> ''
                GROUP BY channel_language, channel_name
            )
            SELECT 
                channel_language, 
                channel_name, 
                satellite_count
            FROM ChannelRankings
            WHERE ranking <= 5
            ORDER BY channel_language, ranking;
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results  # Returns the results to be handled by calling function (e.g., display in Streamlit)
        except Error as e:
            print(f"Error: {e}")
            return []  # Return an empty list on error
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()


def list_channels_by_filters(satellite_name, video_type, language, region):
    """List channels filtered by satellite, video type (HD/SD), language, and region."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT *
            FROM syschannels
            WHERE satellite_name = %s AND video = %s AND channel_language = %s AND TRIM(BOTH '\r' FROM region) = %s;
            """
            cursor.execute(query, (satellite_name, video_type, language, region))
            results = cursor.fetchall()
            if results:
                return results
            else:
                print("No channels found with the specified filters.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()




# make the sidebar first register user interface then next to go to another interface
# Interface for registering a new user
st.title("Lyngsat Database")
st.sidebar.title("User Registration")
name = st.sidebar.text_input("Name")
email = st.sidebar.text_input("Email")
Gender = st.sidebar.selectbox("Gender", options=["M", "F", "Other"])
birthdate = st.sidebar.date_input("Birthdate")
address = st.sidebar.text_input("Address")
# make the region a dropdown list of regions asia, europe, america, atlantic 
region = st.sidebar.selectbox("Region", options=["Asia", "Europe", "America", "Atlantic"])
submit_button = st.sidebar.button("Register User")

if submit_button:
    register_user(name,email,Gender,birthdate,address,region)

# Interface for adding favorite channels
st.sidebar.title("Favorite Channels")
fav_email = st.sidebar.text_input("Favorite User Email")
favorite_channel_id = st.sidebar.number_input("Favorite Channel ID", format="%f")
add_favorite_button = st.sidebar.button("Add Favorite Channel")

if add_favorite_button:
    create_favorites_list(fav_email, favorite_channel_id)


st.write("")


# inteface for top 5 providers and top 5 rockets
if st.sidebar.button("Top 5 Providers"):
    top_five_prov = top_five_providers()
    if top_five_prov:
        df_providers = pd.DataFrame(top_five_prov, columns=['Provider', 'Channel Count', 'Avg. Satellites Per Channel'])
        st.table(df_providers)
    else:
        st.write("No providers found.")

if st.sidebar.button("Top 5 Rockets"):
    top_five_rock = top_five_rockets()
    if top_five_rock:
        df_rockets = pd.DataFrame(top_five_rock, columns=['Rocket', 'Number of Satellites'])
        st.table(df_rockets)
    else:
        st.write("No rockets found.")

if st.sidebar.button("Top Growing Satellites"):
    top_growing_sat = top_growing_satellites()
    if top_growing_sat:
        df_satellites = pd.DataFrame(top_growing_sat, columns=['Satellite', 'Channel Count', 'Days Since Launch', 'Growth Rate'])
        st.table(df_satellites)
    else:
        st.write("No growing satellites found.")


if st.sidebar.button("Top Channels by Language"):
    top_channels_lang = top_channels_by_language()
    if top_channels_lang:
        df_lang = pd.DataFrame(top_channels_lang, columns=['Language', 'Channel', 'Satellite Count'])
        st.table(df_lang)
    else:
        st.write("No channels found by language.")

        
# Interface for listing channels by filters
st.sidebar.title("List Channels by Filters")
satellite_name = st.sidebar.text_input("Satellite Name")
video_type = st.sidebar.selectbox("Video Type", options=["MPEG-4HD", "MPEG-4SD", "MPEG-2SD", "MPEG-4HD 1080"])
language = st.sidebar.selectbox("Language", options=["Eng", "Fre", "Ger", "Ita", "Spa", "Por", "Ara"])
region = st.sidebar.selectbox("Choose Region", options=["asia", "europe", "america", "atlantic"])
filter_button = st.sidebar.button("List Channels")

if filter_button:
    channels = list_channels_by_filters(satellite_name, video_type, language, region)
    if channels:
        df_channels = pd.DataFrame(channels, columns=['Channel Name', 'Satellite Name', 'Position', 'Frequency', 'Polarization', 'Symbol Rate', 'FEC', 'Video Type', 'Language', 'Encryption', 'Region', 'Channel ID'])
        st.table(df_channels)
    else:
        st.write("No channels found with the specified filters.")

        
# add a line break
st.write("")


# Interface for viewing channels
longitude = st.sidebar.number_input("Enter Longitude", format="%f")
if st.sidebar.button("List Viewable Channels"):
    channels = list_viewable_channels(longitude)
    if channels:
        df = pd.DataFrame(channels, columns=['Channel', 'Satellite', 'Position'])
        st.table(df)
    else:
        st.write("No channels found for the given longitude.")

# Interface for showing favorite channels based on user and location
user_email = st.sidebar.text_input("User Email")
user_longitude = st.sidebar.number_input("User Longitude", format="%f")
if st.sidebar.button("Show Favorite Channels"):
    favorites = show_user_favorite_channels(user_email, user_longitude)
    if favorites:
        df_favorites = pd.DataFrame(favorites, columns=['Email', 'Channel', 'Frequency', 'Satellite', 'Encryption'])
        st.table(df_favorites)
    else:
        st.write("No favorite channels found for this user at the given longitude.")


