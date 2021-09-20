
# Import libraries
import time
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os

end_of_game = None  # Set if the user ends the game.

# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = None
led = None
eeprom = ES2EEPROMUtils.ES2EEPROM()

actual = 0 # The number user has to guess
guess = 0  # The guess by user

total_scores = 0
score_count = 0

eeprom_scores = [] # Array storing fetched scores!

# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game, actual
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
        menu()
    elif option == "P":
        end_of_game = False
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        actual = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):

    print("There are {} scores. Here are the top 3!".format(count))

    count = 1
    position = 0 # skip the "how many scores" byte.

    for data in raw_data:
        if (position == 1):
            position += 1
        else:
            if(count == 4):
                break
            else:
                print( "{} - {} : {} guesses".format(count, data[0], data[1]) )
                count += 1

    pass


# Setup Pins
def setup():

    global buzzer, led, LED_value, LED_accuracy, btn_increase, btn_submit    

    # Setup board mode
    GPIO.setmode(GPIO.BOARD)
    	
    # Setup regular GPIO
    # Setting up the buttons
    GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	
    #Setting up the LEDs    	
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(13, GPIO.OUT)
    GPIO.setup(15, GPIO.OUT)
    GPIO.setup(32, GPIO.OUT)

    # Setup the transistor
    GPIO.setup(33, GPIO.OUT)

    # Setup PWM channels
    led = GPIO.PWM(32, 50)	
    buzzer = GPIO.PWM(33, 0.01)

    # Setting all pins to low
    GPIO.output(11, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)
    GPIO.output(15, GPIO.LOW)
    GPIO.output(33, GPIO.LOW)

    # Setup debouncing and callbacks
    GPIO.add_event_detect(16, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=200)
    GPIO.add_event_detect(18, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)

    # One-time clear of scores. --> Done by running EEPROM python class


def fetch_scores():
    # Each reg = 8 bits (1 byte). 
    # Each block has 4 regs

    # This function returns an int, then array of score arrays [[name, score], [name, score]]

    # Get number of scores
    num_scores = eeprom.read_byte(0)

    # Get scores 
    scores = []

    for i in range(1, num_scores + 1):

        # Stores current score in array
        current_score_arr = []

        score = eeprom.read_block(i, 4) # Read next score (32 bits - 4 words)

        # Get letters to create name. Might be bug here!!
        l1 = chr(score[0])
        l2 = chr(score[1])
        l3 = chr(score[2])
        
        name = l1 + l2 + l3
        #print("Your name is: " + str(name))

        current_score_arr.append(str(name))
        current_score_arr.append(score[3])

        scores.append(current_score_arr)

    return num_scores, scores


# Save high scores
def save_scores():

    global eeprom_scores, total_scores, score_count

    # fetch scores
    total_scores, eeprom_scores = fetch_scores() 

    name = input("Enter your 3 letter name: \n")
    while len(name) > 3 or len(name) < 3:
        print("The name your entered wasn't 3 letters.")
        name = input("Enter your 3 letter name: \n")  
    
    new_score = [name[:3], score_count] 
    eeprom_scores.append(new_score) 

    # sort scores based off guess count (x[1]) - second element in array
    sorted_arr = sorted( eeprom_scores, key=lambda x: x[1] )

    # increase total number of scores 
    eeprom.write_byte(0, total_scores + 1) 

    # write all scores back ([byte, byte, byte, byte, byte...])
    # contains all scores following eachother (char, char, char, int, char, char, char, int)
    all_scores = []

    for score in sorted_arr: 

        # user name
        for i in range(3): 
            all_scores.append( ord(score[0][i]) )

        # user score
        all_scores.append(score[1])

    eeprom.write_block(1, all_scores) # write them all in one go


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess


    global L1, L2, L3

    # Find the current_number and increment it
    current_number = L3*(2**2) + L2*(2) + L1
    current_number += 1

    # Now update values of LED values
    # First, set all to 0 by default
    L1 = 0
    L2 = 0
    L3 = 0
    
    if(current_number > 7):
        current_number = 0
        L1 = 0
        L2 = 0
        L3 = 0
	
    else:
        if(current_number - 2**2 >= 0):
            L3 = 1
            current_number = current_number - 2**2

        if(current_number - 2 >= 0):
            L2 = 1
            current_number = current_number - 2

        if(current_number - 1 >= 0):
            L1 = 1
            current_number = current_number - 1

    if(current_number != 0):
        print("huge error lol")


    GPIO.output(11, L1)
    GPIO.output(13, L2)
    GPIO.output(15, L3)



# Guess button
def btn_guess_pressed(channel):
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    
    global L1, L2, L3, actual, guess, score_count, LED_value, end_of_game

    guess = L1 * 1 + L2 * 2 + L3 * 2**2

    start_time = time.time()

    while GPIO.input(channel) == 0: # Wait for the button up
        pass

    timeElapsed = time.time() - start_time
    buttonStatus = 1    

    if .5 <= timeElapsed < 2:       
        buttonStatus = 1        # Submit case
    elif 3 <= timeElapsed:         
        buttonStatus = 2      # Menu


    if(buttonStatus == 1):
	
        score_count+=1

        print("You guessed " + str(guess))

        if(guess == actual):
            print("Correct!")
            
            # stop buzzer
            buzzer.stop()

            # stop LEDs
            led.stop()
            GPIO.output(LED_value, GPIO.LOW)

            save_scores()
            end_of_game = True
            menu()

        else:
            print("Wrong!")

            trigger_buzzer()
            accuracy_leds()

    elif buttonStatus == 2:
        GPIO.output(LED_value, GPIO.LOW)
        buzzer.stop()
        led.stop()
        end_of_game = True
        menu()


# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    global led, actual, guess
    brightness = 0
    led.start(brightness)

    if actual > guess:
        brightness = (guess / actual) * 100
        led.ChangeDutyCycle(brightness)

    elif actual < guess:
    	brightness = ((8 - guess) / (8 - actual)) * 100
    	led.ChangeDutyCycle(brightness)

    pass

# Sound Buzzer
def trigger_buzzer():
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
    global buzzer, actual, guess

    frequency = 0.5

    diff = abs(actual - guess)

    if diff == 3:
        frequency = 1
    elif diff == 2:
        frequency = 2
    elif diff == 1:
        frequency = 4

    buzzer.start(10)
    buzzer.ChangeFrequency(frequency)

    pass


if __name__ == "__main__":
    global L1
    global L2
    global L3
    global current_number

    L1 = 0
    L2 = 0
    L3 = 0
    current_number = 0

    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
