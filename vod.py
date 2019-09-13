from spritekit import *
import vector, arrow
from vector import Vector as V
from random import *

class RaceGame:
  
  playfield = Size(2000, 2000)
  #playfield = (21,21)
  #cell_size = 100
  #start_cell = (10,10)
  buoy_amount = 4
  rock_amount = 100
  rock_min = 20
  rock_max = 40
  rock_velocity_max = 50
  rock_angular_max = 2
  
  object_category = 1
  ship_category = 1+2
  buoy_contact = 2 # Detect ship
  buoy_collision = 0 # Not colliding
  
  def __init__(self, scene):
    self.scene = scene
    self.scene.game = self
    self.visited = 0
    
    pf = self.playfield
    
    self.scene.set_edge_loop(
      -pf.width/2, -pf.height/2,
      pf.width, pf.height)
    BoxNode(pf,
      no_body=True,
      alpha=0.3,
      glow_width=20,
      parent=self.scene
    )
    
    self.cells_to_a_side = math.ceil(math.sqrt(self.rock_amount*1.5+self.buoy_amount+1))
    self.cell_size = self.playfield/self.cells_to_a_side
    half_cells = math.floor(self.cells_to_a_side/2)
    self.cells = [
      (x,y) 
      for x in range(-half_cells, half_cells) 
      for y in range(-half_cells, half_cells)
    ]
    self.cells.remove((0,0))
    
    buoy_possibilities = [
      (x,y) for (x,y) in self.cells
      if V(x,y).magnitude > half_cells/4
    ]
    self.buoys = []
    for pos in sample(buoy_possibilities, self.buoy_amount):
      self.cells.remove(pos)
      self.place_buoy(pos)
      
    for pos in sample(self.cells, self.rock_amount):
      self.cells.remove(pos)
      self.place_rock(pos)
      
    self.place_ship()
    
    self.add_hud_elements()
    
  def add_hud_elements(self):
    self.scene.compass = Node(
      z_position=1,
      alpha=0.5,
      parent=self.scene.ship
    )    
    CircleNode(2,
      fill_color='red',
      line_color='red',
      no_body=True,
      hidden=True,
      position=(30,0),
      parent=self.scene.compass
    )
    self.set_compass_constraint()
      
  def set_compass_constraint(self):
    c = Constraint.orient_to_node(
      self.buoys[self.visited]
    )
    c.reference_node = self.scene.ship
    self.scene.compass.constraints = [c]
    
    A = Action
    self.buoys[self.visited].run_action(
      A.forever([
        A.scale_to(1.2, timing=A.EASE_IN_OUT),
        A.scale_to(1.0, timing=A.EASE_IN_OUT),
      ]),
      'pulse'
    )
    
  def place_ship(self):
    self.scene.ship = Ship(
      category_bitmask=self.ship_category,
      collision_bitmask=self.object_category,
      contect_bitmask=self.buoy_contact,
      rotation=math.pi/4, 
      parent=self.scene)
    self.scene.camera.add_constraint(Constraint.distance_to_node(self.scene.ship, Range.constant(0)))
    
  def place_buoy(self, cell):
    position = self.pos_in_cell(cell)
    buoy = CircleNode(20,
      category_bitmask=self.buoy_contact,
      collision_bitmask=self.buoy_collision,
      fill_color='black',
      line_color='red',
      alpha=0.5,
      glow_width=10,
      z_position=-1,
      dynamic=False,
      position=position,
      parent=self.scene)
    self.buoys.append(buoy)
    LabelNode(text=str(len(self.buoys)),
      alpha=1.0,
      vertical_alignment=LabelNode.ALIGN_MIDDLE,
      position=position,
      parent=self.scene
    )
    if len(self.buoys) == 1:
      buoy.contact_bitmask = self.buoy_contact
    
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
      category_bitmask=self.object_category,
      collision_bitmask=self.object_category,
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
    self.time = LabelNode('', 
      anchor_point=(1,1),
      camera_anchor=Anchor((1,1), (-20,-50)),
      font=('Courier', 16),
      alpha=0.5,
      z_position=1,
      alignment = LabelNode.ALIGN_RIGHT,
      vertical_alignment = LabelNode.ALIGN_TOP,
      parent=self.camera)
    self.camera.layers.append(Layer(
      Texture('images/spacetile_transparent.PNG'), pan_factor=0.2, alpha=0.4))
    #self.camera.layers.append(Layer(
    #  Texture('images/spacetile_bottom.jpg'),
    #  pan_factor=0))
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
    if not self.initialized:
      self.start_time = ct
      return
    
    if self.game.visited < self.game.buoy_amount: 
      elapsed = arrow.get(ct - self.start_time)
      self.time.text = elapsed.format('m:ss:SS')
    
    if len(self.touch_thrust) > 0:
      self.ship.trigger_thrust(self.ship.rotation, self.ship.velocity)

      thrust = vector.Vector(
        self.ship.thrust, 0
      )
      thrust.radians = self.ship.rotation
      self.ship.apply_force((thrust.x, thrust.y))
      #lead = vector.Vector(self.ship.velocity)
      #lead.magnitude = min(lead.magnitude, 100)
      #self.camera_spot.run_action(
      #  Action.move_to(tuple(lead), duration=2.0), 'lead'
      #)
      #self.last_thrust = ct
    
    self.camera.update_layers()
    
  def contact(self, a, b):
    buoy_hit = self.game.buoys[self.game.visited]
    buoy_hit.contact_bitmask = 0
    buoy_hit.line_color = 'green'
    buoy_hit.stop_actions()
    
    self.game.visited += 1
    
    if self.game.visited < self.game.buoy_amount: 
      self.game.buoys[self.game.visited].contact_bitmask = self.game.buoy_contact
      self.game.set_compass_constraint()
    else:
      l = ui.Label(text=self.time.text,
        text_color='white',
        font=('Courier', 32),
        alignment=ui.ALIGN_CENTER,
      )
      l.size_to_fit()
      l.center=self.view.bounds.center()
      self.view.add_subview(l)
      self.run_action(Action.fade_out(duration=2))
    
    
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
    
scene = RaceScene(
  physics=SpacePhysics,
  #physics_debug=True,
)

game = RaceGame(scene)
      
run(scene, 'full_screen', hide_title_bar=True)

scene.camera.scale = 1.5
