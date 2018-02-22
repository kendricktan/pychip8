import sys
import sdl2.ext

sdl2.ext.init()

window = sdl2.ext.Window("Hello World!", size=(640, 480))
window.show()

if __name__ == '__main__':
    sdl2.ext.init()

    window = sdl2.ext.Window("Hello World!", size=(640, 480))
    window.show()

    while True:
        try:
            pass
        except KeyboardInterrupt:
            break