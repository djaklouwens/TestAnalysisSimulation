import winsound
import time
import datetime as dt

def play_sound(duration:int=300, freq:float=800, repetitions:int=5, pause=50):
    '''Play beeping sound to alert user
    
    :param duration: Duration [ms] of a single beep 
    :type duration: float
    :param freq: Frequency in [Hz] of beep, in range 37 to 32,767
    :type freq: float
    :param repetitions: Number of beeps
    :type repetitions: int
    :param pause: Duration [ms] of a pause between beeps 
    :type pause: float
    :return: N/A
    :rtype: NoneType

    '''
    for i in range(repetitions):
        winsound.Beep(freq, duration)
        time.sleep(pause/1000)

def print_status(message=''):
    if message == '': message = 'okay'
    print(f'{dt.datetime.now():%H:%M} - {message}')

if __name__ == '__main__':
    play_sound()
    print_status()