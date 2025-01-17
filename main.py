from PyQt6 import QtWidgets, uic
import sys
import sqlite3
import os  # <-- Add this import
from dotenv import load_dotenv  # <-- Add this import
from huggingface_hub import InferenceClient

# Load environment variables from .env file
load_dotenv()  # <-- Add this line

# Initialize the Hugging Face client for movie suggestions
client = InferenceClient(
    "microsoft/Phi-3-mini-4k-instruct",
    token=os.getenv("HUGGING_FACE_TOKEN"),  # <-- Load token from environment
)


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainApp, self).__init__()
        uic.loadUi('mainWindow.ui', self)  # Load the main window UI

        # Connect buttons to the respective screens
        self.pushButton = self.findChild(QtWidgets.QPushButton, 'pushButton')  # Button for movie suggestion
        self.pushButton_2 = self.findChild(QtWidgets.QPushButton, 'pushButton_2')  # Button for watchlist

        # Set button functionality
        self.pushButton.clicked.connect(self.open_movie_suggestion_dialog)
        self.pushButton_2.clicked.connect(self.open_watchlist_dialog)  # For the watchlist dialog

        #Set background image for main window
        self.setStyleSheet("""
                    QMainWindow {
                        background-image: url('mainbacksmall.jpg');
                        background-position: center;
                        background-repeat: no-repeat;
                    }
                """)


    def open_movie_suggestion_dialog(self):
        self.suggestion_dialog = MovieSuggestionDialog()
        self.suggestion_dialog.exec()  # Open as a modal dialog

    def open_watchlist_dialog(self):
        # Open the watchlist dialog with error handling
        try:
            self.watchlist_dialog = WatchlistDialog()
            self.watchlist_dialog.exec()  # Open as a modal dialog
        except Exception as e:
            print(f"Failed to open watchlist dialog: {e}")

class MovieSuggestionDialog(QtWidgets.QDialog):
    def __init__(self):
        super(MovieSuggestionDialog, self).__init__()
        uic.loadUi('SuggestDialog.ui', self)

        # Access UI elements
        self.lineEdit = self.findChild(QtWidgets.QLineEdit, 'lineEdit')  # Input field for movie name
        self.pushButton = self.findChild(QtWidgets.QPushButton, 'pushButton')  # Button to suggest movies
        self.listWidget = self.findChild(QtWidgets.QListWidget, 'listWidget')  # List widget for displaying suggestions

        # Connect the "Suggest" button to the movie suggestion function
        self.pushButton.clicked.connect(self.suggest_movies)

        # Set background image for movie suggestion dialog
        self.setStyleSheet("""
                            QDialog {
                                background-image: url('doorSuggest.jpg');
                                background-position: center;
                                background-repeat: no-repeat;
                            }
                        """)


    def suggest_movies(self):
        movie_name = self.lineEdit.text()
        if movie_name:
            # Call the AI API to get similar movies
            suggestions = self.get_similar_movies_from_api(movie_name)
            self.display_suggestions(suggestions)

    def get_similar_movies_from_api(self, movie_name):
        try:
            response = client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": f"you are a movie expert. suggest five movies similar to {movie_name}. just name the five movies without any explanation. number the movies from 1 to 5."
                }],
                max_tokens=500,
                stream=False  # We won't use streaming here for simplicity
            )

            # Extract the movie names from the response
            suggestions_text = response.choices[0].message['content']
            # Split the response into separate lines (movies)
            suggestions = suggestions_text.split("\n")
            return suggestions

        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return ["Error in getting suggestions"]

    def display_suggestions(self, suggestions):
        # Clear the list widget before displaying new suggestions
        self.listWidget.clear()
        for movie in suggestions:
            self.listWidget.addItem(movie)

class WatchlistDialog(QtWidgets.QDialog):
    def __init__(self):
        super(WatchlistDialog, self).__init__()
        uic.loadUi('WatchDialog.ui', self)  # Load the watchlist dialog UI

        # Access UI elements
        self.lineEdit = self.findChild(QtWidgets.QLineEdit, 'lineEdit')  # Input field for movie name
        self.pushButton = self.findChild(QtWidgets.QPushButton, 'pushButton')  # Button to add movie
        self.listWidget = self.findChild(QtWidgets.QListWidget, 'listWidget')  # List widget for displaying watchlist

        # Connect the "Add" button to the function that adds the movie to the watchlist
        self.pushButton.clicked.connect(self.add_movie_to_watchlist)

        # Load any existing watchlist items from the database on startup
        self.load_watchlist()

        # Set background image for Watchlist dialog
        self.setStyleSheet("""
                                QDialog {
                                    background-image: url('WatchlistDialog.jpg');
                                    background-position: center;
                                    background-repeat: no-repeat;
                                }
                            """)


    def add_movie_to_watchlist(self):
        # Get the movie name from the input field
        movie_name = self.lineEdit.text()

        # Ensure the movie name isn't empty
        if movie_name:
            # Add the movie to the list widget
            self.listWidget.addItem(movie_name)

            # Save the movie to the database
            self.save_movie_to_db(movie_name)

            # Clear the input field after adding
            self.lineEdit.clear()

    def load_watchlist(self):
        # Connect to the SQLite database with error handling
        try:
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()

            # Retrieve all movies from the database
            cursor.execute("SELECT movie_name FROM watchlist")
            movies = cursor.fetchall()

            # Populate the list widget with movies
            for movie in movies:
                self.listWidget.addItem(movie[0])

            # Close the connection
            conn.close()
        except Exception as e:
            print(f"Error loading watchlist: {e}")

    def save_movie_to_db(self, movie_name):
        # Connect to the SQLite database with error handling
        try:
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()

            # Create the watchlist table if it doesn't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS watchlist (
                                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                movie_name TEXT)''')

            # Insert the new movie into the database
            cursor.execute("INSERT INTO watchlist (movie_name) VALUES (?)", (movie_name,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving movie to database: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())
