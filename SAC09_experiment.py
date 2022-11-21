from psychopy import visual, core, event, clock, gui
from psychopy.event import Mouse
import numpy as np
import glob
import sys
import csv
import os
import datetime
import random
import tobii_research as tr

random.seed() # use clock for random seed

# Experiment parameters
winWidth = 1920; winHeight = 1080
exp_code = "SAC09" # Unique experiment code
runET = 0
timeout_time = 10
cuePositions = [[-500, 0], [500, 0]]

# get current date and time as string
x = datetime.datetime.now()
start_time = x.strftime("%y_%m_%d_%H%M")

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in

# GUI for experiment setup and subject details
setupGUI = gui.Dlg(title= exp_code + " Experiment")
setupGUI.addText('Experiment Setup')
setupGUI.addField('Participant Number:', random.randint(1, 999)) # remove random for experiment
setupGUI.addText(' ')  # blank line
setupGUI.addText('Participant details')
setupGUI.addField('Age:')
setupGUI.addField('Gender', choices=["Male", "Female", "Non-binary", "NA", "Other"])
setupGUI.addField('English first language?', choices=["Yes", "No"])
setupGUI.addField('Which alcoholic category do you drink most often?', choices= ["Beer", "Wine", "Spirits", "NA"])
setup_data = setupGUI.show()  # show dialog and wait for OK or Cancel
if setupGUI.OK:  # or if ok_data is not None
    subNum = int(setup_data[0])
    drinkPref = setup_data[4]
    print(type(subNum))
    dataFile = "DATA\ " + exp_code + "_" + start_time + "_s" + f"{subNum:03}" + ".csv" # create csv data file
    kt_dataFile = "DATA\ " + exp_code + "_" + start_time + "_s" + f"{subNum:03}" + "_kt.csv" # create csv data file
    eye_dataFile = "DATA\ " + exp_code + "_" + start_time + "_s" + f"{subNum:03}" + "_eye.csv"  # create csv data file
else:
    print('Setup cancelled')
    core.quit()

dataHeader = ['exp_code', 'pNum', 'drinkPref', 'cue1', 'cue2',
              'cueOrder', 'cueRelevant', 'instruction', 'corRespKey', 'incRespKey', 'accuracy', 'RT']
with open(dataFile, 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(dataHeader)

dataHeader = ['exp_code', 'pNum', 'trial', 'stimulus', 'response', 'accuracy', 'RT']
with open(kt_dataFile, 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(dataHeader)

TS = 0 # variable for PP timestamps
t_phase = 0 # variable for trial phase information

#mouse = Mouse(visible=True)

if runET == 1:
    # connect to eye=tracker
    writeHeader = True

    found_eyetrackers = tr.find_all_eyetrackers()

    my_eyetracker = found_eyetrackers[0]
    print("Address: " + my_eyetracker.address)
    print("Model: " + my_eyetracker.model)
    print("Name (It's OK if this is empty): " + my_eyetracker.device_name)
    print("Serial number: " + my_eyetracker.serial_number)
    print("NEW")

    def gaze_data_callback(gaze_data):
        # Print gaze points of left and right eye
#        print("Left eye: ({gaze_left_eye}) \t Right eye: ({gaze_right_eye})".format(
#            gaze_left_eye=gaze_data['left_gaze_point_on_display_area'],
#            gaze_right_eye=gaze_data['right_gaze_point_on_display_area']))
        with open(eye_dataFile, 'a', newline = '') as f:  # You will need 'wb' mode in Python 2.x

            global writeHeader, trial, t_phase, TS

            gaze_data["trial"] = trial
            gaze_data["trial_phase"] = t_phase
            gaze_data["pp_TS"] = TS

            w = csv.DictWriter(f, gaze_data.keys())
            if writeHeader == True:
                w.writeheader()
                writeHeader = False
            w.writerow(gaze_data)

win = visual.Window(
    size=[winWidth, winHeight],
    units="pix",
    fullscr=False,
    color=[0.5, 0.5, 0.5])

textFeedback = visual.TextStim(win=win, units="pix", pos=[0, -200], color=[-1,-1,-1],
                               font="Arial", height = 30, bold=True)

# read in input files and generate trial sequence

# function for generating trial sequence
def genTrialSeq(design_filename, blocks):
    # read in input files
    stg_design = np.genfromtxt(design_filename, delimiter=',', skip_header = True, dtype = int)
    stg_trials = []

    for b in range(0,blocks):
        newPerm = np.random.permutation(len(stg_design)) # shuffles rows
        stg_trials.append(stg_design[newPerm])

    stg_trials = np.reshape(stg_trials, (-1, 5)) # -1 here signals the missing dimensions, which is auto computed

    return stg_trials

# stage 1 is (8 x blocks) trials

stg1blks = 2
stg2blks = 1

stg1 = genTrialSeq(os.path.join(script_dir, "input_files/designStg1.csv"), stg1blks) # 2nd parameter is blocks

# stage 1 is (16 x blocks) trials
stg2 = genTrialSeq(os.path.join(script_dir, "input_files/designStg2.csv"), stg2blks) # 2nd parameter is blocks

trialSeq = np.concatenate((stg1, stg2)) # combine stg1 and stg2 trial sequences

print(trialSeq)

# # read in image files and create image array for cues
# cue_files_list = glob.glob('img_files\Cue_*.jpg')
# imgArray = [visual.ImageStim(win, img, size = 300) for img in cue_files_list] # create array of images
# imgArray.insert(0, []) # blank element to ensure images start at index 1

# create circle cues
cueCols = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [-1, -1, -1]]
cueColArray = [visual.Circle(win, size=300, edges=256, fillColor=cueCols[cue], colorSpace='rgb') for cue in range(0, 4)] # create array of images
cueColArray  = np.array(cueColArray)
cueShuffle = np.random.permutation(4)
cueColArray = cueColArray[cueShuffle]
#cueArray.insert(0, []) # blank element to ensure images start at index 1

# read in image files and create image array for cues
if drinkPref == "NA":
    drinkPref = np.random.choice(["Beer", "Wine", "Spirits"], size=1)
if drinkPref == "Beer":
    alc_files_list = glob.glob('img_files\grog*.png')
elif drinkPref == "Wine":
    alc_files_list = glob.glob('img_files\wine*.png')
elif drinkPref == "Spirits":
    alc_files_list = glob.glob('img_files\spirits*.png')

drinkPref = setup_data[4] # reset drink preference in case of NA

alc_cues = [visual.ImageStim(win, img, size = 300) for img in alc_files_list] # create array of images
alc_cues = np.array(alc_cues) # convert to no array
cueShuffle = np.random.permutation(2)
alc_cues = alc_cues[cueShuffle]

water_files_list = glob.glob('img_files\water*.png')
water_cues = [visual.ImageStim(win, img, size = 300) for img in water_files_list] # create array of images
water_cues = np.array(water_cues) # convert to no array
cueShuffle = np.random.permutation(2)
water_cues = water_cues[cueShuffle]

#imgArrayCue = np.concatenate((alc_cues, water_cues))
imgArrayCue = cueColArray


# read in instruction slides
instr_files_list = glob.glob('instruction_files\Slide*.PNG')
instrArray = [visual.ImageStim(win, img, size=(winWidth, winHeight)) for img in instr_files_list] # create array of images
timeout_img = instrArray[4] # image for timeout screen
rest_break_img = instrArray[5] # image for rest break screen (not implemented in this task)
debrief_img = instrArray[6] # image for debrief screen

# fixation cross
fixCross = visual.Circle(win, size=20, edges=256, fillColor=[-1,-1,-1], colorSpace='rgb')

# instruction cues
instrNorm = visual.Circle(win, size=100, edges=256, fillColor=[0,0,0], colorSpace='rgb')
instrRev = visual.Rect(win, size=100, fillColor=[0,0,0], colorSpace='rgb')

# response letter stimuli
responseLetter = visual.TextStim(win, color=[-1,-1,-1], font="Arial", height = 30, bold=True, opacity = 0.1, text="K")
responseBack = visual.Rect(win, size = 30, fillColor = [1, 1, 1])

# present the key training instructions
for instr in range(0, 1):
    instrArray[instr].draw()
    win.flip()
    event.waitKeys(keyList=["space"]) # wait for spacebar response

respOptions = np.array(["a", "z", "k", "m"])

runKeyTraining = True
accCnt = 0
kt_trials = 10
while runKeyTraining == True:

    for k in range(0,kt_trials):

        trialResponses = np.random.choice(respOptions, 1) # get random 2 letters to display

        responseLetter.text = trialResponses[0].capitalize()
        responseLetter.pos = [0,0] # draw first/correct letter in the left position
        responseLetter.draw()

        # stimulus on
        TS = win.flip()

        keys = event.waitKeys(keyList=np.append(respOptions, "f10"), timeStamped=TS, maxWait=timeout_time)  # wait for response

        acc = 0 # default
        if keys == None:
            timeout_img.draw()
            win.flip()
            core.wait(2)
            acc = -99
            RT = -99  # this signals a timeout
        else:
            if len(keys) == 1:  # check there is only 1 response key pressed
                RT = keys[0][1]
                if keys[0][0] == "f10":
                    print("Someone pressed the escape key - F10!!!")
                    win.close()
                    sys.exit()

                elif keys[0][0] == trialResponses[0]:
                    feedback = "Correct!"
                    acc = 1
                    accCnt += 1
                else:
                    feedback = "Error!"
                    acc = 0
            else:  # detected there were multiple keys pressed
                feedback = "Error!"
                RT = -99

            # write feedback text to screen
            textFeedback.text = feedback
            textFeedback.draw()
            TS = win.flip()
            core.wait(.5)

        # ITI
        TS = win.flip()
        core.wait(1)

        kt_data = np.array([exp_code, str(subNum), k+1, trialResponses[0], keys[0][0], acc, RT])
        kt_data = kt_data.astype(str)

        with open(kt_dataFile, 'a', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(kt_data)

    # display accuracy
    textFeedback.text = "Key training accuracy = " + str(round(accCnt/kt_trials*100, 1)) + "%"
    textFeedback.draw()
    TS = win.flip()
    keys = event.waitKeys(keyList=np.array(["f1", "r"]))  # wait for spacebar response

    if keys[0] == "f1":
        runKeyTraining = False
    else:
        accCnt = 0 # rerun key training

# present the instructions
for instr in range(1, 3):
    instrArray[instr].draw()
    win.flip()
    event.waitKeys(keyList=["space"]) # wait for spacebar response

phase_2_instructions = stg1blks*8
trialCnt = 0

# turn eye-tracker on
if runET == 1:
    my_eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

for trial in trialSeq:

    trialCnt += 1
    if trialCnt == phase_2_instructions:
        # present the phase 2 instructions
        for instr in range(3, 4):
            instrArray[instr].draw()
            win.flip()
            event.waitKeys(keyList=["space"])  # wait for spacebar response

    # fixation on
    fixCross.draw()
    TS = win.flip()
    t_phase = 1  # start of the "fixation on" phase
    core.wait(1)

    # instruction on
    if trial[4] == 1:
        instrNorm.draw()
    elif trial[4] == 2:
        instrRev.draw()

    fixCross.draw()
    TS = win.flip()
    t_phase = 2  # start of the "instruction on" phase
    core.wait(1)

    # "trial" is the row from trialSeq, containing info on cues/outcomes etc
    cue1 = imgArrayCue[trial[0]-1]
    cue2 = imgArrayCue[trial[1]-1]
    if trial[2] == 1: # left/right orientation
        cue1.pos = cuePositions[0]
        cue2.pos = cuePositions[1]
    else:
        cue1.pos = cuePositions[1]
        cue2.pos = cuePositions[0]
    cue1.draw()
    cue2.draw()

    # write letter response stim on top of cues
    responseBack.pos = cuePositions[0]
    responseBack.draw()
    responseBack.pos = cuePositions[1]
    responseBack.draw()

    trialResponses = np.random.choice(respOptions, size=2, replace=False) # get random 2 letters to display

    if trial[3] == 1:
        responseLetter.text = trialResponses[0].capitalize()
        responseLetter.pos = cuePositions[0] # draw first/correct letter in the left position
        responseLetter.draw()
        responseLetter.text = trialResponses[1].capitalize()
        responseLetter.pos = cuePositions[1] # draw second/incorrect letter in the right position
        responseLetter.draw()
    else:
        responseLetter.text = trialResponses[1].capitalize()
        responseLetter.pos = cuePositions[0] # draw second/incorrect letter in the left position
        responseLetter.draw()
        responseLetter.text = trialResponses[0].capitalize()
        responseLetter.pos = cuePositions[1] # draw first/correct letter in the right position
        responseLetter.draw()

    # stimulus on
    TS = win.flip()
    t_phase = 3  # start of the "stimulus on" phase

    keys = event.waitKeys(keyList=np.append(trialResponses, "f10"), timeStamped=TS, maxWait=timeout_time)  # wait for response

    acc = 0 # default
    if keys == None:
        timeout_img.draw()
        win.flip()
        core.wait(2)
        acc = -99
        RT = -99  # this signals a timeout
    else:
        if len(keys) == 1:  # check there is only 1 response key pressed
            RT = keys[0][1]
            if keys[0][0] == "f10":
                print("Someone pressed the escape key - F10!!!")
                win.close()
                sys.exit()
            elif keys[0][0] == trialResponses[0]:
                acc = 1
            elif keys[0][0] == trialResponses[1]:
                acc = 0
        else:  # detected there were multiple keys pressed
            feedback = "Error!"
            RT = -99

        # write feedback text to screen
        if acc == 0:
            textFeedback.text = "Error!"
            textFeedback.color = [1,-1,-1]
            textFeedback.draw()
            TS = win.flip()
            t_phase = 4  # response made / feedback on phase
            core.wait(2)

    # ITI
    TS = win.flip()
    t_phase = 5  # feedback off, start of ITI phase
    core.wait(1)

    # write details to csv
    trial_data = np.append(trial, [trialResponses[0], trialResponses[1], acc, RT])
    trial_data = trial_data.astype(str)
    print(trial_data)
    trial_data = np.insert(trial_data, 0, [exp_code, str(subNum), drinkPref])

    with open(dataFile, 'a', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(trial_data)

# turn eye-tracker off
if runET == 1:
    my_eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)

debrief_img.draw()
win.flip()
event.waitKeys(keyList=["space"]) # wait for spacebar response

win.close()
