import curses
import sys
import pandas as pd
import os
import subprocess
from unidecode import unidecode


class DataBaseball:
    def __init__(self):
        # Show all columns when displaying player stats.
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 800)

        # Master file that has the player's name corresponding to their playerID.
        self.people_file = os.path.join('baseballdatabank-2023.1', 'core', 'People.csv')

        # Pertinent files
        self.batting_file = os.path.join('baseballdatabank-2023.1', 'core', 'Batting.csv')
        self.fielding_file = os.path.join('baseballdatabank-2023.1', 'core', 'Fielding.csv')
        self.pitching_file = os.path.join('baseballdatabank-2023.1', 'core', 'Pitching.csv')

        # Reads the csv files into the form of a data frame.
        self.people_df = pd.read_csv(self.people_file)
        self.batting_df = pd.read_csv(self.batting_file)
        self.fielding_df = pd.read_csv(self.fielding_file)
        self.pitching_df = pd.read_csv(self.pitching_file)

        self.toggle = True

    def setToggle(self, toggle):
        self.toggle = toggle

    def getToggle(self):
        return self.toggle

    def normalize_string(self, text):
        if pd.isna(text):  # Return an empty string for NaN values
            return ""
        return unidecode(text)

    def starting_menu(self, stdscr):
        curses.curs_set(0)  # Hide the cursor
        current_row = 0

        while True:
            stdscr.clear()
            if self.getToggle():  # Toggle Menu with extra information.
                menu_options = [
                    "1. Tutorial",
                    "2. Toggle Extra Information [ON]",
                    "3. Random Player [Generate a random MLB player's name]",
                    "4. Player Stats [Return the stats of a specified MLB player]",
                    "5. Exit"
                ]
            else:  # Toggle Menu without extra info.
                menu_options = [
                    "1. Tutorial",
                    "2. Toggle Extra Information [OFF]",
                    "3. Random Player",
                    "4. Player Stats",
                    "5. Exit"
                ]

            # Print menu
            self.print_menu(stdscr, menu_options, current_row)
            key = stdscr.getch()

            # Allows arrow keys to navigate menu.
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                self.handle_menu_selection(stdscr, current_row)
                if current_row != 1:  # If not toggling, wait for a keypress after action
                    stdscr.getch()

    def print_menu(self, stdscr, menu_options, current_row):
        stdscr.clear()
        intro_text = ("Welcome to DataBaseball! This is my program DataBaseball that retrieves\n"
                      "Major League Baseball player's or team's statistics.\n"
                      "Navigate the main menu using the arrow keys, and press enter to proceed.\n")
        stdscr.addstr(0, 0, intro_text)
        y_offset = intro_text.count('\n') + 1

        for idx, option in enumerate(menu_options):
            x = 0   # Can't move horizontally
            y = idx + y_offset  # Vertical menu movement
            if idx == current_row:
                stdscr.addstr(y, x, option, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)
        stdscr.refresh()

    def handle_menu_selection(self, stdscr, selection):
        stdscr.clear()

        if selection == 4:  # Exit program
            curses.endwin()
            sys.exit(0)
        elif selection == 0:  # Tutorial
            stdscr.addstr(0, 0, "----- Tutorial -----\n"
                                "1. Type in '3' and a random player's name should be generated, for example 'Shohei Ohtani'\n"
                                "2. Type in '5', then type in 'Shohei Ohtani' and his stats in his MLB career should appear.\n"
                                "Press any key to return.")
            stdscr.refresh()
        elif selection == 1:  # Toggle
            self.setToggle(not self.toggle)
            if self.toggle:
                msg = "The extra information has been toggled off\n"
            else:
                msg = "The extra information has been toggled on\n"
            stdscr.addstr(0, 0, msg + "Press any key to return.")
            stdscr.refresh()
        elif selection == 2:  # Random MLB player
            random_name = subprocess.run(['python', 'Microservice.py'], capture_output=True, text=True)
            stdscr.addstr(0, 0, f'Random MLB player: {random_name.stdout.strip()}\nPress any key to return.')
            stdscr.refresh()
        elif selection == 3:  # Player stats
            stdscr.clear()
            stdscr.addstr(0, 0, "Enter player's name: ")
            curses.echo()
            input_name = stdscr.getstr(0, 20, 60).decode().strip()
            curses.noecho()

            result = self.search_for_player(stdscr, input_name)
            if isinstance(result, pd.DataFrame):    # If there are multiple matches, list the names out.
                playerID = self.navigate_and_select_match(stdscr, result)
            else:   # If there's only 1 match, that player in the next if statement will directly show his stats.
                playerID = result

            if playerID:    # Show the stats of the player selected in the menu or directly typed in.
                self.display_player_stats(stdscr, playerID)

    def search_for_player(self, stdscr, input_name):
        normalized_name = self.normalize_string(input_name).lower()
        matches = self.people_df[
            self.people_df[['nameFirst', 'nameLast']].apply(
                lambda x: normalized_name in ' '.join(x.fillna('').astype(str)).lower(), axis=1)
        ][['playerID', 'nameFirst', 'nameLast', 'debut', 'finalGame']]

        # Extract the year from debut and finalGame
        matches['debutYear'] = pd.to_datetime(matches['debut']).dt.year.astype('Int64')
        matches['finalYear'] = pd.to_datetime(matches['finalGame']).dt.year.astype('Int64')

        if matches.empty:   # Name not found
            stdscr.addstr(1, 0, "Our database was unable to find that player's name, please try again. Press any key to continue.")
            stdscr.refresh()
            stdscr.getch()
            return None
        elif len(matches) == 1:
            return matches.iloc[0]['playerID']
        else:
            return matches.reset_index(drop=True)

    def navigate_and_select_match(self, stdscr, matches):
        current_row = 0
        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()  # Get the max dimensions of the terminal

            for idx, match in matches.iterrows():
                player_name = f"{match['nameFirst']} {match['nameLast']}"
                # Formatting years to remove the decimal.
                debut_year = str(match['debutYear']) if not pd.isnull(match['debutYear']) else "N/A"
                final_year = str(match['finalYear']) if not pd.isnull(match['finalYear']) else "Present"
                active_years = f"({debut_year} - {final_year})"
                display_str = f"{idx + 1}. {player_name} {active_years}"

                # Keeping the writting within the boundaries.
                if idx < max_y - 2:  # space for the prompt
                    if idx == current_row:
                        stdscr.addstr(idx, 0, display_str[:max_x - 1],
                                      curses.A_REVERSE)  # Truncate and highlight
                    else:
                        stdscr.addstr(idx, 0, display_str[:max_x - 1])  # Truncate
                else:
                    break

            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < min(len(matches), max_y - 2) - 1:
                current_row += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                playerID = matches.iloc[current_row]['playerID']
                return playerID

    def search_and_display_player_stats(self, stdscr, first_name, last_name):
        player = self.people_df[(self.people_df['nameFirst'].str.lower() == first_name.lower()) &
                                (self.people_df['nameLast'].str.lower() == last_name.lower())]

        if player.empty:
            stdscr.addstr(1, 0, "Player not found.")
            stdscr.refresh()
            return

        playerID = player.iloc[0]['playerID']

        batting_stats = self.batting_df[self.batting_df['playerID'] == playerID]

        if batting_stats.empty:
            stats_info = "No batting stats available."
        else:
            # Format batting stats
            stats_info = "BATTING STATS:\n"
            stats_info += "Year  Team  G  AB  R  H  HR  RBI\n"
            for index, row in batting_stats.iterrows():
                stats_info += f"{row['yearID']}  {row['teamID']}  {row['G']}  {row['AB']}  {row['R']}  {row['H']}  {row['HR']}  {row['RBI']}\n"

        stdscr.clear()
        stdscr.addstr(0, 0, f"Displaying stats for {first_name} {last_name}:\n")
        stdscr.addstr(2, 0, stats_info)
        stdscr.refresh()

    def display_player_stats(self, stdscr, playerID):
        # Fetch player's bio and stats
        player_bio = self.people_df[self.people_df['playerID'] == playerID].iloc[0]
        birthDate = f"{int(player_bio['birthMonth'])}/{int(player_bio['birthDay'])}/{int(player_bio['birthYear'])}"
        bio_paragraph = f"{player_bio['nameFirst']} {player_bio['nameLast']} was born in {player_bio['birthCity']}, {player_bio['birthState']}, {player_bio['birthCountry']} on {birthDate}."
        if not pd.isnull(player_bio['deathYear']):
            bio_paragraph += f" Unfortunately, they passed away in {int(player_bio['deathYear'])}."

        # Display the player's bio
        stdscr.clear()
        y_pos = 0
        stdscr.addstr(y_pos, 0, bio_paragraph)
        y_pos += 2

        def display_stats_category(df, category_name, columns):
            nonlocal y_pos
            if not df.empty:
                stdscr.addstr(y_pos, 0, f"{category_name}:")
                y_pos += 1

                col_widths = [max(len(str(df[col].max())), len(col)) for col in columns]

                # Display headers
                header = "".join([f"{col.ljust(width + 2)}" for col, width in zip(columns, col_widths)])
                stdscr.addstr(y_pos, 0, header)
                y_pos += 1

                # Display each stat row
                for _, row in df.iterrows():
                    line = "".join([f"{str(row[col]).ljust(width + 2)}" for col, width in zip(columns, col_widths)])
                    stdscr.addstr(y_pos, 0, line)
                    y_pos += 1

                    if y_pos >= curses.LINES - 1: break

                y_pos += 1  # Extra space after each category

        # Display stats
        batting_columns = ['yearID', 'teamID', 'G', 'AB', 'R', 'H', 'HR', 'RBI']
        display_stats_category(self.batting_df[self.batting_df['playerID'] == playerID], "Batting Stats",
                               batting_columns)

        fielding_columns = ['yearID', 'teamID', 'G', 'A', 'E', 'DP']
        display_stats_category(self.fielding_df[self.fielding_df['playerID'] == playerID], "Fielding Stats",
                               fielding_columns)

        pitching_columns = ['yearID', 'teamID', 'W', 'L', 'ERA', 'G', 'SV', 'SO']
        display_stats_category(self.pitching_df[self.pitching_df['playerID'] == playerID], "Pitching Stats",
                               pitching_columns)

        stdscr.refresh()
        stdscr.getch()

    def main(self):
        curses.wrapper(self.starting_menu)


if __name__ == "__main__":
    x = DataBaseball()
    x.main()
