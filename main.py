import os
import random

import pygame
import pygame_menu
import sys
import json


class App:

    def __init__(self, size=(850, 600), fps=1, level=1):
        # общие настройки
        self.running = False
        self.screen = pygame.display.set_mode(size)
        self.fps = fps
        self.counter = 0
        self.width, self.height = size
        self.action = False
        self.direction = (None, 'right')
        self.block_cords_for_apple = []
        self.snake_cords_for_apple = []
        self.apple = None
        self.flag = None

        # змея - это массив из объектов Body
        self.snake = [Body((200, 300), (None, 'right'), 'head'),
                      Body((200, 250), (None, 'right')),
                      Body((200, 200), (None, 'right'), 'tail')]

        # настройка уровня и объектов
        self.level = 'data/' + str(level) + '.txt'
        self.objects = None

        # настройка заднего фона
        self.bg = load_image("bg.png")
        self.screen.blit(self.bg, (0, 0))

        # инициализация игры
        pygame.init()
        pygame.display.set_caption('Змейка')

        # инициализация главного меню
        self.menu = pygame_menu.Menu('Змейка', size[0], size[1], theme=pygame_menu.themes.THEME_ORANGE)
        self.menu.add.button('Начать игру', self.run)
        self.menu.add.selector('Выберите уровень:', [('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5)],
                               onchange=self.set_level)
        self.menu.add.selector('Выберите скорость:', [('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5),
                                                      ('6', 6), ('7', 7)],
                               onchange=self.set_speed)
        self.menu.add.button('Выйти', pygame_menu.events.EXIT)

    def move(self):
        if self.action or self.flag:  # обработка поворота
            # меняем голову на тело (с поворотом)
            self.snake[0].type = 'body'
            if self.direction[1]:
                self.snake[0].direction = (self.direction[1], self.snake[0].direction[0])
            else:
                self.snake[0].direction = (self.direction[0], self.snake[0].direction[1])
            self.snake[0].define_image()

            # удаляем хвост и назначаем новый
            if not self.flag:
                self.snake[-1].kill()
                self.snake.pop()
                self.snake[-1].type = 'tail'
                self.snake[-1].define_image()
                load_background(self.screen, self.bg)
            else:
                self.flag = False

            # добавляем новую голову
            if self.direction[1] == 'right':
                self.snake.insert(0,
                                  (Body((self.snake[0].cords[0], self.snake[0].cords[1] + 50), self.direction, 'head')))
            elif self.direction[1] == 'left':
                self.snake.insert(0,
                                  (Body((self.snake[0].cords[0], self.snake[0].cords[1] - 50), self.direction, 'head')))
            elif self.direction[0] == 'up':
                self.snake.insert(0,
                                  (Body((self.snake[0].cords[0] - 50, self.snake[0].cords[1]), self.direction, 'head')))
            else:
                self.snake.insert(0,
                                  (Body((self.snake[0].cords[0] + 50, self.snake[0].cords[1]), self.direction, 'head')))
        else:
            # запоминаем голову и добавляем ее со сдвигом
            k = self.snake[0]
            if self.direction[1] == 'right':
                self.snake.insert(0, (Body((k.cords[0], k.cords[1] + 50), k.direction, 'head')))
            elif self.direction[1] == 'left':
                self.snake.insert(0, (Body((k.cords[0], k.cords[1] - 50), k.direction, 'head')))
            elif self.direction[0] == 'up':
                self.snake.insert(0, (Body((k.cords[0] - 50, k.cords[1]), k.direction, 'head')))
            elif self.direction[0] == 'down':
                self.snake.insert(0, (Body((k.cords[0] + 50, k.cords[1]), k.direction, 'head')))

            # меняем старую голову на тело
            self.snake[1].type = 'body'
            self.snake[1].define_image()

            # удаляем хвост и назначаем новый
            self.snake[-1].kill()
            self.snake.pop()
            self.snake[-1].type = 'tail'
            self.snake[-1].define_image()
        load_background(self.screen, self.bg)

    def run(self):
        load_background(self.screen, self.bg)  # отрисовка травы на фоне
        self.objects = generate_level(self.level, self.width)  # массив хранит все спрайты
        if not self.block_cords_for_apple:
            self.block_cords_for_apple = [(x.rect[0], x.rect[1]) for x in self.objects]
        for i in self.snake:
            self.snake_cords_for_apple.append((i.cords[0], i.cords[1]))
        self.running = True

        self.apple = generate_apple(self.block_cords_for_apple + self.snake_cords_for_apple)
        self.snake_cords_for_apple = []
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and not self.action:
                    if event.key == pygame.K_LEFT:
                        if self.snake[0].direction[1] != 'right':
                            self.action = True
                            self.direction = (None, 'left')
                    if event.key == pygame.K_RIGHT:
                        if self.snake[0].direction[1] != 'left':
                            self.action = True
                            self.direction = (None, 'right')
                    if event.key == pygame.K_UP:
                        if self.snake[0].direction[0] != 'down':
                            self.action = True
                            self.direction = ('up', None)
                    if event.key == pygame.K_DOWN:
                        if self.snake[0].direction[0] != 'up':
                            self.action = True
                            self.direction = ('down', None)
            pygame.time.Clock().tick(20)
            if self.counter == 20 // self.fps:
                self.move()
                draw_sprites(self.screen)

                pygame.display.flip()

                self.counter = 0
                self.action = False

                self.check_collision()
            self.counter += 1
        for obj in self.objects:  # очистка объектов
            obj.kill()

    def check_collision(self):  # проверка столкновений
        if pygame.sprite.spritecollideany(self.snake[0], border_group):  # столкновение со стеной
            restart_game(self)
        elif pygame.sprite.spritecollideany(self.snake[0], apple_group):
            self.apple.kill()
            for i in self.snake:
                self.snake_cords_for_apple.append((i.cords[1], i.cords[0]))
            self.apple = generate_apple(self.block_cords_for_apple + self.snake_cords_for_apple)
            self.snake_cords_for_apple = []
            self.flag = True
        for tile in self.snake[1:]:  # столкновение с телом
            if self.snake[0].rect == tile.rect:
                restart_game(self)

    def start_menu(self):
        self.menu.mainloop(self.screen)

    def set_level(self, values, number):
        self.level = 'data/' + str(number) + '.txt'

    def set_speed(self, values, number):
        self.fps = number


class Border(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(border_group)
        self.image = load_image('box.png')
        self.rect = self.image.get_rect().move(
            50 * pos_x, 50 * pos_y)


class Apple(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(apple_group)
        self.image = load_image('apple.png')
        self.rect = self.image.get_rect().move(
            pos_x, pos_y)

    def update(self, x, y):
        self.rect = self.image.get_rect().move(
            x, y)


class Body(pygame.sprite.Sprite):
    def __init__(self, cords, direction, body_type='body'):
        super().__init__(body_group)

        self.cords = cords
        self.direction = direction
        self.type = body_type

        self.image = None
        self.rect = None
        self.define_image()

    def define_image(self):
        self.image = self.type
        if not self.direction[0]:
            self.image += '_' + self.direction[1] + '.png'
        elif not self.direction[1]:
            self.image += '_' + self.direction[0] + '.png'
        else:
            self.image += '_' + self.direction[1] + '_' + self.direction[0] + '.png'
        self.image = load_image(self.image)
        self.rect = self.image.get_rect().move(self.cords[1], self.cords[0])


def generate_level(filename, width):  # загрузка уровня через текстовой документ
    objects = []
    with open(filename, 'r') as mapFile:  # обработка текстовика
        level_map = [line.strip() for line in mapFile][:(width // 50) + 1]
    level = list(map(lambda x: x.ljust(width, '.'), level_map))
    for y in range(len(level)):  # генерация уровня
        for x in range(len(level[y])):
            if level[y][x] == '#':
                objects.append(Border(x, y))
    return objects


def load_image(name):  # загрузка изображения
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


def load_background(surface, bg):
    for r in range(0, surface.get_size()[0] + 1, 50):
        for c in range(0, surface.get_size()[1] + 1, 50):
            surface.blit(bg, (r, c))


def draw_sprites(display):
    border_group.draw(display)
    snake_group.draw(display)
    apple_group.draw(display)
    body_group.draw(display)


def generate_apple(objects_list):
    map_apple = []
    for i in range(0, settings['width'], 50):
        for j in range(0, settings['height'], 50):
            if (i, j) not in objects_list:
                map_apple.append((i, j))
    random_pos = random.choice(map_apple)
    apple = Apple(random_pos[0], random_pos[1])
    return apple


def restart_game(app):
    app.apple.kill()
    for obj in app.snake:
        obj.kill()
    for obj in app.objects:
        obj.kill()
    app = App((settings['width'], settings['height']), settings['fps'])
    app.start_menu()
    app.run()


border_group = pygame.sprite.Group()
grass_group = pygame.sprite.Group()
snake_group = pygame.sprite.Group()
apple_group = pygame.sprite.Group()
body_group = pygame.sprite.Group()

settings = open("settings.json", "r")
settings = json.loads(settings.read())
game = App((settings['width'], settings['height']), settings['fps'])
game.start_menu()
game.run()
