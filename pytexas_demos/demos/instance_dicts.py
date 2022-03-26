from dicts import print_dict_all, print_dict

class Animal:
    def __init__(self, name, species, age, sound = None, smell = None):
        self.name = name
        self.species = species
        self.age = age
        if sound:
            self.sound = sound
        if smell:
            self.smell = smell

    def mute(self):
        del self.sound


flipper = Animal("Flipper", "Fish", 1)
print_dict_all(flipper.__dict__)  # keys refcount 2, size 104

funky = Animal("Funky", "Skunk", 3, smell="Smelly")
print_dict_all(funky.__dict__)  # keys refcount 3, size 104

milo = Animal("Milo", "Cat", 5, sound="Meow")
print_dict_all(milo.__dict__)  # keys refcount 2, sizeo 360??

# we had to resize, so key sharing has stopped. refcount has dropped.
print_dict(funky.__dict__)

# flipper again...
flipper = Animal("Flipper", "Fish", 1)
print_dict_all(flipper.__dict__)  # not shared, size is 232!

# re-start the interpreter
milo = Animal("Milo", "Cat", 5, sound="Meow")
print_dict_all(milo.__dict__)  # shared

milo.mute()
print_dict_all(milo.__dict__)  # not shared

milo = Animal("Milo", "Cat", 5, sound="Meow")
print_dict_all(milo.__dict__)  # a new instance isn't shared, either
