import numpy as np
import pygame as pg
from random import randint, gauss

pg.init()
pg.font.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

SCREEN_SIZE = (800, 600)


def rand_color():
    return (randint(0, 255), randint(0, 255), randint(0, 255))

class GameObject:

    def move(self):
        pass
    
    def draw(self, screen):
        pass  


class Shell(GameObject):
    '''
    The ball class. Creates a ball, controls it's movement and implement it's rendering.
    '''
    def __init__(self, coord, velocity, radius=20, color=None):
        '''
        Constructor method. Initializes ball's parameters and initial values.
        '''
        self.coord = coord
        self.velocity = velocity
        if color == None:
            color = rand_color()
        self.color = color
        self.radius = radius
        self.is_alive = True

    def check_corners(self, refl_ort=0.8, refl_par=0.9):
        '''
        Reflects ball's velocity when ball bumps into the screen corners. Implemetns inelastic rebounce.
        '''
        for i in range(2):
            if self.coord[i] < self.radius:
                self.coord[i] = self.radius
                self.velocity[i] = -int(self.velocity[i] * refl_ort)
                self.velocity[1-i] = int(self.velocity[1-i] * refl_par)
            elif self.coord[i] > SCREEN_SIZE[i] - self.radius:
                self.coord[i] = SCREEN_SIZE[i] - self.radius
                self.velocity[i] = -int(self.velocity[i] * refl_ort)
                self.velocity[1-i] = int(self.velocity[1-i] * refl_par)

    def move(self, time=1, gravity=0):
        '''
        Moves the ball according to it's velocity and time step.
        Changes the ball's velocity due to gravitational force.
        '''
        self.velocity[1] += gravity
        for i in range(2):
            self.coord[i] += time * self.velocity[i]
        self.check_corners()
        if self.velocity[0]**2 + self.velocity[1]**2 < 2**2 and self.coord[1] > SCREEN_SIZE[1] - 2*self.radius:
            self.is_alive = False

    def draw(self, screen):
        '''
        Draws the ball on appropriate surface.
        '''
        pg.draw.circle(screen, self.color, self.coord, self.radius)


class Cannon(GameObject):
    '''
    Cannon class. Manages it's renderring, movement and striking.
    '''
    def __init__(self, coord=[SCREEN_SIZE[0]//2, SCREEN_SIZE[1]-30], angle=0, max_pow=50, min_pow=10, color=RED):
        '''
        Constructor method. Sets coordinate, direction, minimum and maximum power and color of the gun.
        '''
        self.coord = coord
        self.angle = angle
        self.max_pow = max_pow
        self.min_pow = min_pow
        self.color = color
        self.active = False
        self.pow = min_pow
    
    def activate(self):
        '''
        Activates gun's charge.
        '''
        self.active = True

    def gain(self, increment=2):
        '''
        Increases current gun charge power.
        '''
        if self.active and self.pow < self.max_pow:
            self.pow += increment

    def strike(self):
        '''
        Creates ball, according to gun's direction and current charge power.
        '''
        vel = self.pow
        angle = self.angle
        ball = Shell(list(self.coord), [int(vel * np.cos(angle)), int(vel * np.sin(angle))])
        self.pow = self.min_pow
        self.active = False
        return ball
        
    def set_angle(self, target_pos):
        '''
        Sets gun's direction to target position.
        '''
        self.angle = np.arctan2(target_pos[1] - self.coord[1], target_pos[0] - self.coord[0])

    def move(self, increment):
        '''
        Changes horizontal position of the gun.
        '''
        if (self.coord[0] > 30 or increment > 0) and (self.coord[0] < SCREEN_SIZE[0] - 30 or increment < 0):
            self.coord[0] += increment

    def draw(self, screen):
        '''
        Draws the gun on the screen.
        '''
        # draw base of the tank
        cannon_base_pos = self.coord
        tank_base_width, tank_base_height = 50, 30
        pg.draw.rect(screen, (255, 255, 255), 
                     (cannon_base_pos[0]-tank_base_width//2, cannon_base_pos[1], 
                      tank_base_width, tank_base_height)
        )

        # draw gun
        gun_shape = []
        vec_1 = np.array([int(5*np.cos(self.angle - np.pi/2)), int(5*np.sin(self.angle - np.pi/2))])
        vec_2 = np.array([int(self.pow*np.cos(self.angle)), int(self.pow*np.sin(self.angle))])
        gun_pos = np.array(self.coord)
        gun_shape.append((gun_pos + vec_1).tolist())
        gun_shape.append((gun_pos + vec_1 + vec_2).tolist())
        gun_shape.append((gun_pos + vec_2 - vec_1).tolist())
        gun_shape.append((gun_pos - vec_1).tolist())
        pg.draw.polygon(screen, self.color, gun_shape)

        # draw tank cannon cover
        tank_ball_radius = 15
        pg.draw.circle(screen, (200, 200, 200), (cannon_base_pos[0], cannon_base_pos[1]+5), tank_ball_radius)

class Target(GameObject):
    '''
    Target class. Creates target, manages it's rendering and collision with a ball event.
    '''
    def __init__(self, coord=None, color=None, radius=30):
        '''
        Constructor method. Sets coordinate, color and radius of the target.
        '''
        if coord == None:
            coord = [randint(radius, SCREEN_SIZE[0] - radius), randint(radius, SCREEN_SIZE[1] - radius)]
        self.coord = coord
        self.radius = radius

        if color == None:
            color = rand_color()
        self.color = color

    def check_collision(self, shell):
        '''
        Checks whether the shell bumps into target.
        '''
        dist = sum([(self.coord[i] - shell.coord[i])**2 for i in range(2)])**0.5
        min_dist = self.radius + shell.radius
        return dist <= min_dist

    def draw(self, screen):
        '''
        Draws the target on the screen
        '''
        pg.draw.circle(screen, self.color, self.coord, self.radius)

    def move(self):
        """
        This type of target can't move at all.
        :return: None
        """
        pass

class MovingTargets(Target):
    def __init__(self, coord=None, color=None, radius=30):
        super().__init__(coord, color, radius)
        self.x_velocity = randint(-2, +2)
        self.y_velocity = randint(-2, +2)
    
    def move(self):
        self.coord[0] += self.x_velocity
        self.coord[1] += self.y_velocity

        # if hit border, change velocity
        if self.coord[0] + self.radius > SCREEN_SIZE[0] or self.coord[0] - self.radius < 0:
            self.x_velocity *= -1
        if self.coord[1] + self.radius > SCREEN_SIZE[1] or self.coord[1] - self.radius < 0:
            self.y_velocity *= -1


class ScoreTable:
    '''
    Score table class.
    '''
    def __init__(self, target_destroyed=0, shell_used=0):
        self.target_destroyed = target_destroyed
        self.shell_used = shell_used
        self.font = pg.font.SysFont("dejavusansmono", 25)

    def score(self):
        '''
        Score calculation method.
        '''
        return self.target_destroyed - self.shell_used

    def draw(self, screen):
        score_surface = []
        score_surface.append(self.font.render("Destroyed: {}".format(self.target_destroyed), True, WHITE))
        score_surface.append(self.font.render("Balls used: {}".format(self.shell_used), True, WHITE))
        score_surface.append(self.font.render("Total: {}".format(self.score()), True, RED))
        for i in range(3):
            screen.blit(score_surface[i], [10, 10+30*i])


class Manager:
    '''
    Class that manages events' handling, ball's motion and collision, target creation, etc.
    '''
    def __init__(self, num_of_targets=1, gravity=2):
        self.shells = []
        self.gun = Cannon()
        self.targets = []
        self.score_table = ScoreTable()
        self.num_of_targets = num_of_targets
        self.gravity = gravity
        self.new_mission()

    def new_mission(self):
        '''
        Adds new targets.
        '''
        for _ in range(self.num_of_targets):
            # as score goes up, the radius of the target shrink
            self.targets.append(
                MovingTargets(radius=randint(
                    max(1, 30 - 2 * max(0, self.score_table.score())),
                    30 - max(0, self.score_table.score()))
                )
            )   
            self.targets.append(
                Target(radius=randint(
                    max(1, 30 - 2 * max(0, self.score_table.score())),
                    30 - max(0, self.score_table.score()))
                )
            )


    def process(self, events, screen):
        '''
        Runs all necessary method for each iteration. Adds new targets, if previous are destroyed.
        '''
        done = self.handle_events(events)

        if pg.mouse.get_focused():
            mouse_pos = pg.mouse.get_pos()
            self.gun.set_angle(mouse_pos)
        
        self.move()
        self.collide()
        self.draw(screen)

        if len(self.targets) == 0 and len(self.shells) == 0:
            self.new_mission()

        return done

    def handle_events(self, events):
        '''
        Handles events from keyboard, mouse, etc.
        '''
        done = False
        for event in events:
            if event.type == pg.QUIT:
                done = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.gun.activate()
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.shells.append(self.gun.strike())
                    self.score_table.shell_used += 1
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.gun.move(-5)
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.gun.move(5)

        return done

    def draw(self, screen):
        '''
        Runs balls', gun's, targets' and score table's drawing method.
        '''
        for ball in self.shells:
            ball.draw(screen)
        for target in self.targets:
            target.draw(screen)
        self.gun.draw(screen)
        self.score_table.draw(screen)

    def move(self):
        '''
        Runs shells' and gun's movement method, removes dead shells.
        '''
        dead_shells = []
        for i, shell in enumerate(self.shells):
            shell.move(gravity=self.gravity)
            if not shell.is_alive:
                dead_shells.append(i)
        for i in reversed(dead_shells):
            self.shells.pop(i)
        for i, target in enumerate(self.targets):
            target.move()
        self.gun.gain()

    def collide(self):
        '''
        Checks whether balls bump into targets, sets balls' alive trigger.
        '''
        collisions = []
        targets_c = []
        for i, ball in enumerate(self.shells):
            for j, target in enumerate(self.targets):
                if target.check_collision(ball):
                    collisions.append([i, j])
                    targets_c.append(j)
        targets_c.sort()
        for j in reversed(targets_c):
            self.score_table.target_destroyed += 1
            self.targets.pop(j)

def main() -> None:
    screen = pg.display.set_mode(SCREEN_SIZE)
    pg.display.set_caption("The gun of Khiryanov")

    done = False
    clock = pg.time.Clock()

    mgr = Manager(num_of_targets=3)

    while not done:
        clock.tick(30)
        screen.fill(BLACK)

        done = mgr.process(pg.event.get(), screen)

        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    main()