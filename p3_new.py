
# Import libraries
import time
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game

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

totalscores = 0
scorecount = 0

end_of_game = None
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
    global end_of_game
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format

    counts = 1
    place = 0

    for data in raw_data:
        if place == 1:
            place += 1
        else :
            print("{} - {} took {} guesses".format(counts, data[0],data[1]))
            counts +=1
        if counts == 4:
            break

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
    buzzer = GPIO.PWM(33, 50)

    # Setting all pins to low
    GPIO.setup(11, GPIO.LOW)
    GPIO.setup(13, GPIO.LOW)
    GPIO.setup(15, GPIO.LOW)
    GPIO.setup(32, GPIO.OUT)
    GPIO.output(33, GPIO.LOW)

    # Setup debouncing and callbacks
    GPIO.add_event_detect(16, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=200)
    GPIO.add_event_detect(18, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)

    pass


# Load high scores **CHANGE VAR NAMES**
def fetch_scores():
    # get however many scores there are
    score_count = eeprom.read_byte(0)

    # array of scores and names taken from the EEPROM into a 2D array
    scores = []
    # Get the scores
    # convert the codes back to ascii
    for i in range(1, score_count+1):
        reset = []  #ensures that reset is emptied before every iteration
        score = eeprom.read_block(i,4) # This will read registers 1 to 4 from block i and place it into scores

        # Convert the "letter" registers into char values to generate words
        letter1 = chr(score[0])
        letter2 = chr(score[1])
        letter3 = chr(score[2])

        # Turn the letters into a word for the user name
        name = letter1 + letter2 + letter3
        # Adds the name formed and scores to an empty reset array as 2 entries
        reset.append(name)
        reset.append(score[3])

        scores.append(reset) #Adds the values from reset to scorelist, to form a 2D array of Name and Score
     # return back the results
    return score_count, scores


# Save high scores
def save_scores():
    global eeprom_scores, totalscores, scorecount
    # fetch scores
    totalscores, eeprom_scores = fetch_scores()
    eeprom.write_byte(0, totalscores+ 1)  # update total amount of scores
    name = input("Enter your 3 letter name: \n")  # Prompt user for their Name
    inputScore = [name[:3], scorecount] # Holder for the name and score number to be sent to the eeprom
    eeprom_scores.append(inputScore) #Adds the name and score counts to the score values array

    #sort
    sortedArray = sorted(eeprom_scores, key=lambda x: x[1])

    #Write the given values to the EEPROM
    transmittedvalues = []
    for scores in sortedArray: #adds the name and score number to a matrix which is written into the eeprom
        for i in range(3): #loops through 3 letters in sortedArray and converts it into binary for the EEPROM
            transmittedvalues.append(ord(scores[0][i]))
        transmittedvalues.append(scores[1])
    eeprom.write_block(1,transmittedvalues)
    pass


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
    
    global L1, L2, L3, actual, guess, scorecount, LED_value

    actual = generate_number()
    guess = L1 * 1 + L2 * 2 + L3 * 2**2

    print(guess)

    start_time = time.time()

    while GPIO.input(channel) == 0: # Wait for the button up
        pass

    timeElapsed = time.time() - start_time
    buttonStatus = 1    

    if .5 <= timeElapsed < 3:       
        buttonStatus = 1        # Submit case
    elif 3 <= timeElapsed:         
        buttonStatus = 2      # Menu
    if(buttonStatus == 1):
	# submit

        scorecount+=1

        print("You guessed " + str(guess))

        if(guess == actual):
            print("Correct!")
            GPIO.output(LED_value, False) 
            GPIO.output(33,GPIO.LOW)  
            save_scores()
            menu()

        else:
            print("Wrong!")
            trigger_buzzer()
            accuracy_leds()
        
    else:
        menu()


# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    global led, actual, guess
    brightness = 0

    if actual > guess:
        brightness = guess / actual * 100
    elif actual < guess:
    	brightness = (8 - guess) / (8 - actual) * 100
    else:
        brightness = 100

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

    frequency = 0

    diff = abs(actual - guess)

    if diff == 3:
        frequency = 1
    elif diff == 2:
        frequency = 2
    elif diff == 1:
        frequency = 4

    buzzer.start(50)
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
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
