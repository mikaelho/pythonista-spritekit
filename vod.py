from spritekit import *
import vector
from vector import Vector as V
from random import *

class RaceGame:
  
  playfield = Size(2000,2000)
  #playfield = (21,21)
  #cell_size = 100
  #start_cell = (10,10)
  buoy_amount = 4
  rock_amount = 100
  rock_min = 20
  rock_max = 40
  rock_velocity_max = 50
  rock_angular_max = 2
  
  def __init__(self, scene):
    self.scene = scene
    pf = self.playfield
    self.scene.set_edge_loop(
      -pf.width/2, -pf.height/2,
      pf.width, pf.height)
    
    self.cells_to_a_side = math.ceil(math.sqrt(self.rock_amount*1.5+self.buoy_amount+1))
    self.cell_size = self.playfield/self.cells_to_a_side
    half_cells = math.floor(self.cells_to_a_side/2)
    self.cells = [
      (x,y) 
      for x in range(-half_cells, half_cells) 
      for y in range(-half_cells, half_cells)
    ]
    self.cells.remove((0,0))
    
    '''
    buoy_possibilities = [
      (x,y) for (x,y) in self.cells
      if V(x,y).magnitude > 10 and V(x,y).magnitude < 20]
      
    self.buoys = []
    for pos in sample(buoy_possibilities, self.buoy_amount):
      self.cells.remove(pos)
      self.place_buoy(pos)
    '''
      
    for pos in sample(self.cells, self.rock_amount):
      self.cells.remove(pos)
      self.place_rock(pos)
      
    self.place_ship()
    
  def place_ship(self):
    pass
    
  def place_buoy(self, cell):
    pass
    
  def place_rock(self, cell):
    position = self.pos_in_cell(cell)
    r = randint(self.rock_min, self.rock_max)
    magnitude = randint(int(.3*r), int(.7*r))
    points = []
    for a in range(0, 340, 20):
      magnitude = max(
        min(
          magnitude + randint(
            int(-.2*r), int(.2*r)), 
          r),
        .2*r)
      point = V(magnitude, 0)
      point.degrees = a
      points.append(tuple(point))
    points.append(points[0])
    
    ShapeNode(points,
      smooth=True,
      fill_color='black',
      position=position,
      velocity=(
        randint(-self.rock_velocity_max, self.rock_velocity_max), 
        randint(-self.rock_velocity_max, self.rock_velocity_max)),
      angular_velocity = randint(-self.rock_angular_max, self.rock_angular_max),
      parent=self.scene)
    
  def pos_in_cell(self, cell):
    return tuple((
      cell[i] * self.cell_size[i] +
      randint(0, math.floor(self.cell_size[i]))
      for i in [0, 1]
    ))
    
    
class RaceScene(Scene):
  
  def __init__(self, **kwargs):
    self.initialized = False
    super().__init__(can_pan=False, can_pinch=True, **kwargs)
    self.background_color = 'black'
    self.touch_thrust = []
    self.touch_rotate = []
    self.touch_rotate_start = 0
    self.multitouch_enabled = True
    self.anchor_point = (0.5,0.5)
    self.camera = CameraNode(parent=self)
    #self.prev_camera_pos = self.camera.position
    self.scaffold = Node(parent=self)
    self.ship = Ship(
      rotation=math.pi/4, 
      parent=self)
    self.camera_spot = Node(parent=self.scaffold)
    self.camera.layers.append(Layer(
      Texture('images/spacetile_transparent.PNG'), pan_factor=0.2, alpha=0.4))
    #self.camera.layers.append(Layer(
    #  Texture('images/spacetile_bottom.jpg'),
    #  pan_factor=0))
    self.scaffold.add_constraint(Constraint.distance_to_node(self.ship, Range.constant(0)))
    self.camera.add_constraint(Constraint.distance_to_node(self.camera_spot, Range.limits(-25, 25)))
    self.initialized = True
    
  def touch_began(self, t):
    if t.location.x > self.camera.position.x:
      self.touch_thrust.append(t.touch_id)
    else:
      self.touch_rotate.append(t.touch_id)
      if len(self.touch_rotate) == 1:
        self.touch_rotate_start = t.location.x
        
  def touch_moved(self, t):
    if len(self.touch_rotate) == 1 and t.touch_id == self.touch_rotate[0]:
      self.ship.angular_velocity = 0
      self.ship.rotation += (t.location.x - t.prev_location.x)/50
    
  def touch_ended(self, t):
    if t.touch_id in self.touch_thrust:
      self.touch_thrust.remove(t.touch_id)
    if t.touch_id in self.touch_rotate:
      self.touch_rotate.remove(t.touch_id)
    
  def update(self, ct):
    if not self.initialized: return
    
    if len(self.touch_thrust) > 0:
      self.ship.trigger_thrust(self.ship.rotation, self.ship.velocity)

      thrust = vector.Vector(
        self.ship.thrust, 0
      )
      thrust.radians = self.ship.rotation
      self.ship.apply_force((thrust.x, thrust.y))
      lead = vector.Vector(self.ship.velocity)
      lead.magnitude = min(lead.magnitude, 100)
      self.camera_spot.run_action(
        Action.move_to(tuple(lead), duration=2.0), 'lead'
      )
      #self.camera_spot.position = tuple(lead)
      self.last_thrust = ct
    
    self.camera.update_layers()
    
    
class Ship(ShapeNode):
  
  def __init__(self, **kwargs):
    self.thrust = 5
    
    p = ui.Path()
    p.line_to(-25,10)
    p.line_to(-25,-10)
    p.close()
    #super().__init__('spc:PlayerShip1Orange',**kwargs)
    super().__init__(p,
      line_color='white',
      fill_color='black',
      **kwargs,
      )
    self.thrust_texture = Texture('shp:Explosion03')

  def trigger_thrust(self, heading, velocity):
    #return
    EmitterNode(parent=self,
      target_node=self.parent,
      particle_birth_rate = 10,
      num_particles_to_emit = 2,
      particle_life_time = 0.1,
      particle_size = Size(10,10),
      particle_alpha = 0.5,
      particle_alpha_range = 0.1,
      particle_alpha_speed = -1.0,
      emission_angle = heading - math.pi,
      emission_angle_range = 0.2,
      emission_distance = 50,
      particle_speed = 1000,
      particle_color = 'white',
      
      #particle_texture = self.thrust_texture.texture
    )
    
scene = RaceScene(physics=SpacePhysics, physics_debug=True)

game = RaceGame(scene)
      
run(scene, 'full_screen', hide_title_bar=True)

scene.camera.scale = 1.5
