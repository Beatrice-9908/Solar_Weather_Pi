import sys
from threading import Thread
import drawbuffers as db

refresh_thread = Thread(target = db.refresh_data)
button_action_thread = Thread(target = db.button_action)
refresh_loop_thread = Thread(target = db.refresh_loop, daemon=True)

def main():
    
    try:
        db.initial()
        db.main_loop()

    except KeyboardInterrupt:
        print("Keyboard Interrupt... Exited")
        sys.exit()
    except Exception as e:
        print("Error... exiting")
        sys.exit()


refresh_thread.start()
main()
button_action_thread.start()
refresh_loop_thread.start()
