import random, importlib, math

import ui
from objc_util import *
from objc_util import ObjCInstanceMethodProxy
from scene import Rect, Size
import list_callback

try:
  import pygestures
  from scripter import *
except ModuleNotFoundError: pass

load_framework('SpriteKit')

SK_classes = [
  'SKView', 'SKScene', 'SKNode',
  'SKShapeNode', 'SKSpriteNode',
  'SKPhysicsBody',
  'SKCameraNode', 'SKLightNode',
  'SKTexture',
  'SKFieldNode', 'SKRegion',
  'SKConstraint', 'SKRange',
]

for class_name in SK_classes:
  globals()[class_name] = ObjCClass(class_name)

'''
SKView = ObjCClass('SKView')
SKScene = ObjCClass('SKScene')
SKNode = ObjCClass('SKNode')
SKShapeNode = ObjCClass('SKShapeNode')
SKSpriteNode = ObjCClass('SKSpriteNode')
SKFieldNode = ObjCClass('SKFieldNode')
SKCameraNode = ObjCClass('SKCameraNode')
SKPhysicsBody = ObjCClass('SKPhysicsBody')
SKLightNode = ObjCClass('SKLightNode')
SKTexture = ObjCClass('SKTexture')
SKRegion = ObjCClass('SKRegion')
SKConstraint = ObjCClass('SKConstraint') 
SKRange = ObjCClass('SKRange')
'''

def py_to_cg(value):
  if len(value) == 4:
    x, y, w, h = value
    return CGRect(CGPoint(x, y), CGSize(w,h))
  elif len(value) == 2:
    x, y = value
    return CGPoint(x, y)
  elif type(value) == Size:
    w, h = value
    return CGSize(w, h)
    
def cg_to_py(value):
  if type(value) == ObjCInstanceMethodProxy:
    value = value()
  if type(value) == CGPoint:
    return ui.Point(value.x, value.y)
  elif type(value) == CGVector:
    return ui.Point(value.dx, value.dy)
  elif type(value) == CGRect:
    return Rect(
      value.origin.x, value.origin.y,
      value.size.width, value.size.height)
  elif type(value) == CGSize:
    return Size(value.width, value.height)

def prop(func):
  return property(func, func)
  
def node_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      getattr(self.node, attribute_name)(),
    lambda self, value:
      setattr(self.node, attribute_name, value)
  )
  return p
  
def node_relay_set(attribute_name):
  '''Property creator for pass-through physics properties'''
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  p = property(
    lambda self:
      getattr(self.node, attribute_name)(),
    lambda self, value:
      getattr(self.node, set_name)(value)
  )
  return p
  
def convert_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      cg_to_py(getattr(self.node, attribute_name)),
    lambda self, value:
      setattr(self.node, attribute_name, py_to_cg(value))
  )
  return p
  
def convert_relay_readonly(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      cg_to_py(getattr(self.node, attribute_name))
  )
  return p
  
def str_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      str(getattr(self.node, attribute_name)()),
    lambda self, value:
      setattr(self.node, attribute_name, value)
  )
  return p
  
def no_op():
  '''Property that does nothing, used by Scene to masquerade as a regular node. '''
  p = property(
    lambda self:
      None,
    lambda self, value:
      None
  )
  return p
  
def color_prop(self, attribute, *value):
  if value:
    value = ui.parse_color(value[0])
    setattr(self.node, attribute, UIColor.color(red=value[0], green=value[1], blue=value[2], alpha=value[3]))
  else:
    color = getattr(self.node, attribute)()
    return (
      color.red,
      color.green,
      color.blue,
      color.alpha
    )
  
def color_relay(attribute_name):
  p = property(
    lambda self:
      color_prop(self, attribute_name),
    lambda self, value:
      color_prop(self, attribute_name, value)
  )
  return p
  
def physics_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      getattr(self.node.physicsBody(), attribute_name),
    lambda self, value:
      setattr(self.node.physicsBody(), attribute_name, value)
  )
  return p
  
def physics_relay_set(attribute_name):
  '''Property creator for pass-through physics properties'''
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  p = property(
    lambda self:
      getattr(self.node.physicsBody(), attribute_name)(),
    lambda self, value:
      getattr(self.node.physicsBody(), 'set'+attribute_name[0].upper()+attribute_name[1:]+'_')(value)
  )
  return p
  
def boolean_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  get_name = 'is'+attribute_name[0].upper()+attribute_name[1:]
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  p = property(
    lambda self:
      getattr(self.node, get_name)(),
    lambda self, value:
      getattr(self.node, set_name)(value)
  )
  return p
  
def physics_relay_readonly(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      getattr(self.node.physicsBody(), attribute_name)()
  )
  return p
  
def vector_physics_relay(attribute_name):
  p = property(
    lambda self:
      (getattr(self.node.physicsBody(), attribute_name)[0], 
      getattr(self.node.physicsBody(), attribute_name)[1]),
    lambda self, value:
      setattr(self.node.physicsBody(), attribute_name, CGVector(*value))
  )
  return p


class Node:
  
  default_physics = None
  
  def __init__(self, **kwargs):
    self._parent = None
    self._children = []
    self.constraints = list_callback.NotifyList(callback=self._constraint_update)

    if not hasattr(self, 'node'):
      self.node = SKNode.alloc().init()
    self.node.py_node = self
    
    self.paused = False
    self.speed = 1.0
    #self.scene = None
    
    if (self.default_physics is not None and
      not isinstance(self,
        (Scene, CameraNode, FieldNode))):
      for key in dir(self.default_physics()):
        if not key.startswith('_'):
          setattr(self, key, getattr(self.default_physics, key))
    
    for key in kwargs:
      setattr(self, key, kwargs[key])
  
  @prop
  def parent(self, *args):
    if args:
      value = args[0]
      if self._parent is not None:
        self._parent.node.removeChild_(self.node)
        self._parent.children.remove(self)
      self._parent = value
      if value is not None:
        self._parent.node.addChild_(self.node)
        self._parent.children.append(self)
        self.scene = value.scene
      else:
        self.scene = None
    else:
      return self._parent
      
  @property
  def children(self):
    return self._children
  
  def add_constraint(self, constraint):
    self.constraints.append(constraint)
    
  def _constraint_update(self):
    sk_constraints = [
      c.constraint for c in self.constraints]
    self.node.setConstraints_(sk_constraints)
      
  def convert_point_to(self, point, node):
    return cg_to_py(
      self.node.convertPoint_toNode_(
        py_to_cg(point), node.node))
    
  def convert_point_from(self, point, node):
    return cg_to_py(
      self.node.convertPoint_fromNode_(
        py_to_cg(point), node.node))
      
  @prop
  def scale(self, *args):
    if args:
      value = args[0]
      self.scale_x = value
      self.scale_y = value
    else:
      assert self.scale_x == self.scale_y
      return self.scale_x
      
  def set_edge_line(self, frm, to):
    self.node.physicsBody = SKPhysicsBody.bodyWithEdgeFromPoint_toPoint_(
      CGPoint(*frm), CGPoint(*to)
    )
      
  def set_edge_loop(self, x, y, w, h):
    self.node.physicsBody = SKPhysicsBody.bodyWithEdgeLoopFromRect_(
      CGRect(CGPoint(x, y), CGSize(w, h)))
    
  def set_edge_path(self, path):
    cgpath = path.objc_instance.CGPath()
    self.node.physicsBody = SKPhysicsBody.bodyWithEdgeLoopFromPath_(
      cgpath)
  
  affected_by_gravity = physics_relay_set('affectedByGravity')   
  allows_rotation = physics_relay_set('allowsRotation')
  alpha = node_relay('alpha')
  anchor_point = convert_relay('anchorPoint')
  area = physics_relay_readonly('area')
  angular_damping = physics_relay_set('angularDamping')
  angular_velocity = physics_relay_set('angularVelocity')
  background_color = fill_color = color_relay('fillColor')
  bbox = convert_relay_readonly('calculateAccumulatedFrame') 
  bullet_physics = physics_relay_set('usesPreciseCollisionDetection')
  category_bitmask = physics_relay_set('categoryBitMask')
  contact_bitmask = physics_relay_set('contactTestBitMask')
  collision_bitmask = physics_relay_set('collisionBitMask')
  
  density = physics_relay_set('density')
  
  @prop
  def dynamic(self, *args):
    if args:
      value = args[0]
      self.body.setDynamic_(value)
    else:
      return self.body.isDynamic()
  
  #dynamic = physics_relay('isDynamic')
  frame = convert_relay('frame')
  friction = physics_relay_set('friction')
  hidden = node_relay('isHidden')
  linear_damping = physics_relay_set('linearDamping')
  mass = physics_relay_set('mass')
  name = str_relay('name')
  body = node_relay('physicsBody')
  position = convert_relay('position')
  resting = physics_relay_readonly('isResting')
  restitution = physics_relay_set('restitution')
  rotation = node_relay('zRotation')
  scale_x = node_relay('xScale')
  scale_y = node_relay('yScale')
  size = convert_relay('size')
  touch_enabled = node_relay('userInteractionEnabled')
  velocity = vector_physics_relay('velocity')
  z_position = node_relay('zPosition')


class PathNode(Node):
  
  def __init__(self, path=ui.Path(), **kwargs):
    self.node = None
    self.path = path
    super().__init__(**kwargs)
    
  @prop
  def path(self, *args):
    if args:
      value = args[0]
      self._path = path = value
      cgpath = path.objc_instance.CGPath()
      if self.node is None:
        self.node = TouchShapeNode.shapeNodeWithPath_(cgpath)
      else:
        self.node.path = cgpath
      physics = SKPhysicsBody.bodyWithPolygonFromPath_(cgpath)
      if physics is None:
        #texture = view.skview.textureFromNode_(self.node)
        texture = SKView.alloc().init().textureFromNode_(self.node)
        physics = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
      if physics is None:
        raise RuntimeError(f'Could not create physics body for path {path}.')
      self.node.setPhysicsBody_(physics)
    else:
      return self._path
      
  @prop
  def antialiased(self, *args):
    if args:
      value = args[0]
      self.physics_body.setAntialiased_(value)
    else:
      return self.physics_body.isAntialised()
      
  @prop
  def fill_texture(self, *args):
    if args:
      value = args[0]
      if value is not None:
        value = value.texture
      self.node.fillTexture = value
    else:
      value = self.node.fillTexture
      if value is not None:
        value = Texture(value)
      return value
      
  glow_width = node_relay('glowWidth')
  line_color = color_relay('strokeColor')
  line_width = node_relay('lineWidth')


class PointsNode(Node):
  
  def __init__(self, points, smooth=False, **kwargs):
    cg_points = [ py_to_cg(point) for point in points ]

    cg_points_array = (CGPoint * len(cg_points))(*cg_points)
    
    if smooth:
      self.node = SKShapeNode.shapeNodeWithSplinePoints_count_(cg_points_array, len(cg_points), restype=c_void_p, argtypes=[POINTER(CGPoint), c_ulong])

    else:
      self.node = SKShapeNode.shapeNodeWithPoints_count_(cg_points_array, len(cg_points), restype=c_void_p, argtypes=[POINTER(CGPoint), c_ulong])

    texture = SKView.alloc().init().textureFromNode_(self.node)
    self.node = TouchSpriteNode.spriteNodeWithTexture_(texture)
    physics = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
    self.node.setPhysicsBody_(physics)
    
    super().__init__(**kwargs)
    

class BoxNode(PathNode):
  
  def __init__(self, size=(100,100), **kwargs):
    #self.node = None
    w,h = self._size = size
    
    '''
    self.node = node = SKShapeNode.shapeNodeWithRectOfSize_(rect)
    node.physicsBody = SKPhysicsBody.bodyWithRectangleOfSize_(rect)
    '''
    super().__init__(path=ui.Path.rect(-w/2, -h/2, w, h), **kwargs)
    
  @prop
  def size(self, *args):
    if args:
      w, h = self._size = args[0]
      self.path = ui.Path.rect(-w/2, -h/2, w, h)
    else:
      return self._size


class CameraNode(Node):
  
  def __init__(self, **kwargs):
    self.node = SKCameraNode.alloc().init()
    super().__init__(**kwargs)
    
  def visible(self, node):
    return self.node.containsNode_(node.node)
    
  def visible_nodes():
    visible = set()
    for sk_node in self.node.containedNodeSet_():
      visible.add(sk_node.py_node)
    return visible

class CircleNode(PathNode):
  
  def __init__(self, radius=50, **kwargs):
    #self.node = None
    r = self._radius = radius
    '''
    self.node = node = SKShapeNode.shapeNodeWithCircleOfRadius_(radius)
    node.physicsBody = SKPhysicsBody.bodyWithCircleOfRadius_(radius)
    '''
    super().__init__(path=ui.Path.oval(-r, -r, 2*r, 2*r), **kwargs)
    #self.anchor_point = (0.5, 0.)
    #print(self.anchor_point)
    
  @prop
  def radius(self, *args):
    if args:
      self._radius = r = args[0]
      self.path = ui.Path.oval(-r, -r, 2*r, 2*r)
    else:
      return self._radius
    
    
class SpriteNode(Node):
  
  def __init__(self, image, alpha_threshold=None, **kwargs):
    image_texture = Texture(image)
    texture = image_texture.texture
    '''
    if type(image) == ui.Image:
      texture = SKTexture.textureWithImage_(ObjCInstance(image))
    '''
    self.node = TouchSpriteNode.spriteNodeWithTexture_(texture)
    if alpha_threshold is None:
      self.node.physicsBody = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
    else:
      self.node.physicsBody = SKPhysicsBody.bodyWithTexture_alphaThreshold_size_(texture, alpha_threshold, texture.size())
    super().__init__(**kwargs)
    

class FieldNode(Node):
  
  def __init__(self, fieldnode):
    self.node = fieldnode
    super().__init__()
  
  @classmethod
  def drag(cls):
    return FieldNode(SKFieldNode.dragField())
    
  @classmethod
  def electric(cls):
    return FieldNode(SKFieldNode.electricField())
    
  @classmethod
  def linear_gravity(cls, gravity_vector):
    return FieldNode(
      SKFieldNode.linearGravityFieldWithVector_(py_to_cg(gravity_vector)))
    
  @classmethod
  def magnetic(cls):
    return FieldNode(SKFieldNode.magneticField())
    
  @classmethod
  def noise(cls, smoothness, animation_speed):
    return FieldNode(
      SKFieldNode.noiseFieldWithSmoothness_animationSpeed_(
        smoothness,
        animation_speed))
        
  @classmethod
  def radial_gravity(cls):
    return FieldNode(
      SKFieldNode.radialGravityField())
      
  @classmethod
  def spring(cls):
    return FieldNode(
      SKFieldNode.springField())
      
  @classmethod
  def turbulence(cls, smoothness, animation_speed):
    return FieldNode(
      SKFieldNode.turbulenceFieldWithSmoothness_animationSpeed_(
        smoothness,
        animation_speed))
        
  @classmethod
  def velocity_texture(cls, texture):
    assert type(texture) == Texture
    return FieldNode(
      SKFieldNode.velocityFieldWithTexture_(texture.texture))
        
  @classmethod
  def velocity_vector(cls, vector):
    return FieldNode(
      SKFieldNode.velocityFieldWithVector_(py_to_cg(vector)))
      
  @classmethod
  def vortex(cls):
    return FieldNode(SKFieldNode.vortexField())
    
  enabled = boolean_relay('enabled')
  exclusive = boolean_relay('exclusive')
  falloff = node_relay('falloff')
  strength = node_relay('strength')
  
  @prop
  def region(self, *args):
    if args:
      value = args[0]
      assert type(value) == Region
      self.node.setRegion_(value.region)
    else:
      return Region(self.node.region)
  
class Region:
  
  def __init__(self, region):
    if type(region) == Region:
      region = region.region
    self.region = region
    
  @classmethod
  def infinite(cls):
    return Region(SKRegion.infiniteRegion())
    
  @classmethod
  def size(cls, size):
    size = CGSize(*size)
    return Region(SKRegion.alloc().initWithSize_(size))
    
  @classmethod
  def radius(cls, radius):
    return Region(SKRegion.alloc().initWithRadius_(radius))
    
  @classmethod
  def path(cls, path):
    assert type(path) == ui.Path
    return Region(SKRegion.alloc().initWithPath_(path.objc_instance.CGPath()))

  def inverse(self):
    return Region(self.region.inverseRegion())
    
  def difference(self, other):
    assert type(other) == Region
    return Region(self.region.regionByDifferenceFromRegion_(other.region))
    
  def intersection(self, other):
    assert type(other) == Region
    return Region(self.region.regionByIntersectionWithRegion_(other.region))

  def union(self, other):
    assert type(other) == Region
    return Region(self.region.regionByUnionWithRegion_(other.region))
    
  @property
  def path(self):
    return ui.Path()._initWithCGMutablePath_(self.region.path())
    
  def contains(self, point):
    return self.region.containsPoint(py_to_cg(point))
    
    
class Constraint:
  
  def __init__(self, constraint):
    self.constraint = constraint
    
  @prop
  def enabled(self, *args):
    if args:
      value = args[0]
      self.constraint.setEnabled_(value)
    else:
      return self.constraint.enabled()
      
  @prop
  def reference_node(self, *args):
    if args:
      value = args[0]
      assert isinstance(value, Node)
      self.constraint.setReferenceNode_(value, node)
    else:
      return self.constraint.referenceNode().py_node
  
  @classmethod
  def distance_to_node(cls, node, distance):
    assert isinstance(node, Node)
    assert type(distance) == Range
    return Constraint(SKConstraint.distance_toNode_(
      distance.range, node.node))
  
  @classmethod
  def distance_to_point(cls, point, distance):
    point = py_to_cg(point)
    assert type(distance) == Range
    return Constraint(SKConstraint.distance_toPoint_(
      distance.range, point))
  
  @classmethod
  def distance_to_point_in_node(cls, point, node, distance):
    point = py_to_cg(point)
    assert isinstance(node, Node)
    assert type(distance) == Range
    return Constraint(SKConstraint.distance_toPoint_inNode_(
      distance.range, point, node.node))
  
  @classmethod
  def orient_to_node(cls, node, offset):
    assert isinstance(node, Node)
    assert type(offset) == Range
    return Constraint(SKConstraint.orientToNode_offset_(
      node.node, offset.range))
      
  @classmethod
  def orient_to_point(cls, point, offset):
    point = py_to_cg(point)
    assert type(offset) == Range
    return Constraint(SKConstraint.orientToPoint_offset_(
      point, offset.range))
      
  @classmethod
  def orient_to_point_in_node(cls, point, node, offset):
    point = py_to_cg(point)
    assert isinstance(node, Node)
    assert type(offset) == Range
    return Constraint(SKConstraint.orientToPoint_inNode_offset_(
      point, node.node, offset.range))
  
  @classmethod
  def position(cls, x_range, y_range):
    assert type(x_range) == Range
    assert type(y_range) == Range
    return Constraint(SKConstraint.positionX_Y_(
      x_range.range, y_range.range))
      
  @classmethod
  def position_x(cls, x_range):
    assert type(x_range) == Range
    return Constraint(SKConstraint.positionX_(
      x_range.range))
      
  @classmethod
  def position_y(cls, y_range):
    assert type(y_range) == Range
    return Constraint(SKConstraint.positionY_(
      y_range.range))
      
  @classmethod
  def rotation(cls, range):
    assert type(range) == Range
    return Constraint(SKConstraint.zRotation_(
      range.range))
  
  @classmethod
  def scale(cls, scale_range):
    assert type(scale_range) == Range
    return Constraint(SKConstraint.scaleX_scaleY_(
      scale_range.range, scale_range.range))
      
  @classmethod
  def scale_x(cls, x_range):
    assert type(x_range) == Range
    return Constraint(SKConstraint.scaleX_(
      x_range.range))
      
  @classmethod
  def scale_y(cls, y_range):
    assert type(y_range) == Range
    return Constraint(SKConstraint.scaleY_(
      y_range.range))

  
class Range:
  
  def __init__(self, range):
    self.range = range
    
  @property
  def upper_limit(self):
    return self.range.upperLimit()
    
  @property
  def lower_limit(self):
    return self.range.lowerLimit()
    
  @classmethod
  def constant(cls, value):
    return Range(SKRange.rangeWithConstantValue_(value))
    
  @classmethod
  def lower(cls, limit):
    return Range(SKRange.rangeWithLowerLimit_(limit))
    
  @classmethod
  def upper(cls, limit):
    return Range(SKRange.rangeWithUpperLimit_(limit))
    
  @classmethod
  def limits(cls, lower, upper):
    return Range(SKRange.rangeWithLowerLimit_upperLimit_(lower, upper))
    
  @classmethod
  def no_limits(cls):
    return Range(SKRange.rangeWithNoLimits())
    
  @classmethod
  def variance(cls, value, variance):
    return Range(SKRange.rangeWithValue_variance_(value, variance))
    

class SpriteTouch:
  
  def __init__(self, id, touch, node):
    self.touch_id = id
    self.phase = ('began', 'moved', 'stationary', 'ended', 'cancelled')[touch.phase()]
    loc = touch.locationInNode_(node)
    self.location = ui.Point(loc.x, loc.y)
    prev = touch.previousLocationInNode_(node)
    self.prev_location = ui.Point(prev.x, prev.y)
    self.timestamp = touch.timestamp()
    
  def convert_to_view(self, scene):
    self.location = scene.convert_to_view(self.location)
    self.prev_location = scene.convert_to_view(self.prev_location)

def handle_touch(_self, _cmd, _touches, event, py_func_name):
  node = ObjCInstance(_self)

  py_node = node.py_node
  py_func = getattr(py_node, py_func_name, None)
  if py_func is None: return

  touches = ObjCInstance(_touches)
  for touch in touches:
    py_touch = SpriteTouch(int(touch._touchIdentifier()), touch, node)
    py_func(py_touch)

def touchesBegan_withEvent_(_self, _cmd, _touches, event):
  handle_touch(_self, _cmd, _touches, event, 'touch_began')
  
def touchesMoved_withEvent_(_self, _cmd, _touches, event):
  handle_touch(_self, _cmd, _touches, event, 'touch_moved')

def touchesEnded_withEvent_(_self, _cmd, _touches, event):
  handle_touch(_self, _cmd, _touches, event, 'touch_ended')

def update_(_self, _cmd, current_time): 
  if not 'ObjCInstance' in globals():
    return
  scene = ObjCInstance(_self)
  if not hasattr(scene, 'py_node'):
    scene.paused = True
    return
  node = scene.py_node
  if hasattr(node, 'update'):
    node.update(current_time)

def didChangeSize_(_self,_cmd, _oldSize):
  scene = ObjCInstance(_self)
  if hasattr(scene, 'py_node'):
    if scene.py_node.edges:
      v = scene.py_node.view
      scene.py_node.set_edge_loop(
        0, 0, v.width, v.height)
    if hasattr(scene.py_node, 'layout'):
      scene.py_node.layout()

def didBeginContact_(_self, _cmd, _contact):
  scene = ObjCInstance(_self)
  contact = ObjCInstance(_contact)
  if hasattr(scene, 'py_node'):
    node_a = contact.bodyA().node().py_node
    node_b = contact.bodyB().node().py_node
    scene.py_node.contact(node_a, node_b)


SpriteScene = create_objc_class(
'SpriteScene',
SKScene,
methods=[
update_,
didChangeSize_,
touchesBegan_withEvent_,
touchesMoved_withEvent_,
touchesEnded_withEvent_,
didBeginContact_,
],
protocols=['SKPhysicsContactDelegate'])

TouchShapeNode = create_objc_class(
'TouchShapeNode',
SKShapeNode,
methods=[
touchesBegan_withEvent_,
touchesMoved_withEvent_,
touchesEnded_withEvent_,
])

TouchSpriteNode = create_objc_class(
'TouchSpriteNode',
SKSpriteNode,
methods=[
touchesBegan_withEvent_,
touchesMoved_withEvent_,
touchesEnded_withEvent_,
])


class Scene(Node):
  
  def __init__(self, physics=None, touchable=False, physics_debug=False, **kwargs):
    kwargs['physics_debug'] = physics_debug
    self.view = view = TouchableSpriteView(**kwargs) if touchable else SpriteView(**kwargs)
    rect = CGRect(CGPoint(0, 0), CGSize(view.width, view.height))
    self.scene = self
    self.node = scene = SpriteScene.sceneWithSize_(rect.size)
    scene.py_node = self
    view.scene = self
    scene.scaleMode = 3 #resizeFill
    scene.physicsWorld().setContactDelegate_(scene)
    
    if physics is not None:
      Node.default_physics = physics
      if hasattr(physics, 'gravity'):
        self.gravity = physics.gravity
    
    super().__init__(**kwargs)
    
    #if touchable:
    #  self.camera = CameraNode(parent=self)
    view.skview.presentScene_(scene)
    
  def run(self):
    self.view.present()
    
  def setup(self):
    pass
    
  def convert_to_view(self, point):
    return cg_to_py(self.node.convertPointToView_(
      py_to_cg(point)
    ))
    
  def convert_from_view(self, point):
    return cg_to_py(self.node.convertPointFromView_(
      py_to_cg(point)
    ))
    
  @prop
  def bounds(self, *args):
    if args:
      value = args[0]
      raise NotImplementedError('Setting bounds on a scene not supported')
    else:
      x,y,w,h = self.view.frame
      c = self.convert_from_view
      corner = c((x, y+h))
      other = c((x+w, y))
      return Rect(*corner,
      other.x-corner.x, other.y-corner.y)
    
  @prop
  def camera(self, *args):
    if args:
      value = args[0]
      self.node.setCamera_(value.node)
    else:
      return self.node.camera().py_node
      
  def contact(self, node_a, node_b):
    pass
    
  @prop
  def edges(self, *args):
    if args:
      value = args[0]
      if value is None:
        self.node.physicsBody = None
      else:
        self.node.physicsBody = SKPhysicsBody.bodyWithEdgeLoopFromRect_(CGRect(
          CGPoint(0,0),
          CGSize(
            self.view.width,
            self.view.height)))
    else:
      return False
      #self.node.physicsBody() is not None
    
  @prop
  def gravity(self, *args):
    if args:
      value = args[0]
      self.node.physicsWorld().setGravity(value)
    else:
      return self.node.physicsWorld().gravity()
    
  contact_bitmask = no_op()
  background_color = color_relay('backgroundColor')
  
class TouchScene(Scene):
  
  def __init__(self, **kwargs):
    self.viewable_area = None
    super().__init__(**kwargs)
    self.camera = CameraNode(parent=self)
    self.converter = TouchView(
      frame=self.view.bounds, flex='WH', touch_enabled=False, scene=self)
    self.view.add_subview(self.converter)
    
  def touch_began(self, touch):
    touch.convert_to_view(self)
    self.converter.touch_began(touch)
    
  def touch_moved(self, touch):
    touch.convert_to_view(self)
    self.converter.touch_moved(touch)
    
  def touch_ended(self, touch):
    touch.convert_to_view(self)
    self.converter.touch_ended(touch)
    
  @prop
  def viewable_area(self, *args):
    if args:
      value = args[0]
      if type(value) is not Rect:
        if value is not None and len(value) == 4:
          value = Rect(*value)
      self._viewable_area = value
    else:
      return self._viewable_area
  
  def keep_in_viewable_area(self, orig_scale=1):
    if self.viewable_area is None:
      return
    v = self.viewable_area
    b = self.bounds
    if b.x < v.x:
      self.camera.position += (v.x - b.x, 0)
    if b.y < v.y:
      self.camera.position += (0, v.y - b.y)
    if b.max_x > v.max_x:
      self.camera.position -= (b.max_x - v.max_x, 0)
    if b.max_y > v.max_y:
      self.camera.position -= (0, b.max_y - v.max_y)
    if b.width > v.width or b.height > v.height:
      self.camera.scale = orig_scale
    
  '''
  def on_pan(self, g):
    if g.began:
      self.start_camera_position = self.camera.position
      self.start_location = self.convert_to_view(g.location)
      self.start_pos = g.location
    if g.changed:
      new_pos = self.start_pos + g.translation
      relative_start = self.convert_from_view(self.start_location)
      delta = new_pos - relative_start
      self.camera.position = self.start_camera_position - delta
      
  def on_pinch(self, g):
    if g.began:
      self.start_scale = self.camera.scale
      self.start_distance = self.pinch_distance_in_view(g)
    if g.changed:
      scale = self.pinch_distance_in_view(g)/self.start_distance
      print(len(g.touches_in_order))
      focus_start_pos = self.convert_to_view(g.location)
      self.camera.scale = self.start_scale / scale
      focus_new_pos = self.convert_from_view(focus_start_pos)
      self.camera.position -= g.location - focus_new_pos
      
  def pinch_distance_in_view(self, g):
    distance_vector = (
      self.convert_to_view(g.touches_in_order[0].location) -  
      self.convert_to_view(g.touches_in_order[1].location))
    print(abs(distance_vector))
    return abs(distance_vector)
'''
  
class SpriteView(Scripter):

  def __init__(self, physics_debug, **kwargs):
    super().__init__(**kwargs)
    rect = CGRect(CGPoint(0, 0),CGSize(self.width, self.height))
    skview = SKView.alloc().initWithFrame_(rect)
    skview.autoresizingMask = 2 + 16 # WH
    #skview.showsNodeCount = True
    if physics_debug:
      skview.showsPhysics = True
    ObjCInstance(self).addSubview(skview)
    self.skview = skview
    self.multitouch_enabled = True
    self.skview.setMultipleTouchEnabled_(True)
  
  def will_close(self):
    self.scene.node.removeAllChildren()
    # Must pause to stop update_
    self.scene.node.paused = True
    self.scene.node.removeFromParent()
    self.skview.removeFromSuperview()
    self.skview.release()
    self.skview = None
    self.scene.node = None


class TouchView(
  ui.View, pygestures.GestureMixin):
      
  def on_tap(self, g):
    g.location = self.scene.convert_from_view(g.location)
    self.scene.on_tap(g)
    
  def on_pan(self, g):
    if g.began:
      self.start_camera_position = self.scene.camera.position
      self.start_scene_location = self.scene.convert_from_view(g.location)
      self.start_pos = g.location
    if g.changed:
      new_pos = self.start_pos + g.translation
      new_scene_location = self.scene.convert_from_view(new_pos)
      delta = new_scene_location - self.start_scene_location
      prev_camera_pos = self.scene.camera.position
      self.scene.camera.position -= delta
      self.scene.keep_in_viewable_area()

  def on_pinch(self, g):
    if g.began:
      self.start_scale = self.scene.camera.scale
    if g.changed:
      focus_start_pos = self.scene.convert_from_view(g.location)
      orig_scale = self.scene.camera.scale
      self.scene.camera.scale = self.start_scale / g.scale
      focus_new_pos = self.scene.convert_from_view(g.location)
      self.scene.camera.position -= focus_start_pos - focus_new_pos
      self.scene.keep_in_viewable_area(orig_scale)
      
  '''
  def on_rotate(self, g):
    if g.changed:
      delta_rotation = g.prev_rotation - g.rotation
      self.scene.camera.rotation -= math.radians(delta_rotation)
  '''

class BasePhysics:
  affected_by_gravity = True
  allows_rotation = True
  bullet_physics = False
  dynamic = True

class EarthPhysics(BasePhysics):
  gravity = (0, -9.8)
  angular_damping = 0.2
  friction = 0.2
  linear_damping = 0.1
  restitution = 0.2
  
class SpacePhysics(BasePhysics):
  gravity = (0, 0)
  angular_damping = 0.0
  friction = 0.2
  linear_damping = 0.0
  restitution = 1.0
  
class BilliardsPhysics(BasePhysics):
  gravity = (0, 0)
  angular_damping = 0.02
  friction = 0.2
  linear_damping = 0.3
  restitution = 0.6

@on_main_thread
def run(scene, 
  orientation=None, 
  frame_interval=1,
  antialias=False,
  show_fps=False,
  multi_touch=True):
  scene.view.present()
  
class Texture:
  
  def __init__(self, image_data):
    if type(image_data) == str:
      image_data = ui.Image(image_data)
    if type(image_data) == ui.Image:
      self.texture = SKTexture.textureWithImage_(ObjCInstance(image_data))
    elif type(image_data) == Texture:
      self.texture = image_data.texture
    else:
      self.texture = image_data
    
  def crop(self, rect):
    return Texture(SKTexture.textureWithRect_inTexture_(py_to_cg(rect), self.texture))
    

if __name__ == '__main__':
  
  import vector
  
  def random_color():
    return (random.random(), random.random(), random.random())
  
  class TouchCircleNode(CircleNode):
    
    def __init__(self, radius, **kwargs):
      super().__init__(radius, **kwargs)
      self.touch_enabled = True
    
    def touch_ended(self, touch):
      self.fill_color = random_color()
  
  class TestScene(TouchScene):
    
    def __init__(self, **kwargs):
      w,h = ui.get_screen_size()
      va = Rect(-2*w, -h, 4*w, 2*h)
      super().__init__(viewable_area=va, **kwargs)
      b = BoxNode((va[2], va[3]), parent=self, fill_color='blue', dynamic=False)
      b.node.physicsBody = None
      c1 = CircleNode(20, parent=self, fill_color='red', position=(va.x, va.y))
      c2 = CircleNode(20, parent=self, fill_color='red', position=(va.x+va.width, va.y))
      c3 = CircleNode(20, parent=self, fill_color='red', position=(va.x+va.width, va.y+va.height))
      c4 = CircleNode(20, parent=self, fill_color='red', position=(va.x, va.y+va.height))
      #c2 = CircleNode(20, parent=self.camera, dynamic='False', fill_color='green')
      #c2.node.physicsBody = None

      #self.set_edge_loop(-w/2,-h/2,w,h)
      #self.camera.scale = 5
    
    def update(self, timestamp):
      for child in scene.children():
        if child.position().y < 0:
          child.removeFromParent()
          
    def on_tap(self, touch):
      node = random.choice([
        self.create_box_shape,
        self.create_circle_shape,
        self.create_polygon_shape,
        self.create_sprite_node,
        self.create_smooth_shape,
      ])(touch.location)
      node.parent = self
      node.fill_color = random_color()
      node.velocity = (random.randint(-20,20), random.randint(-20,20))
    
    def create_circle_shape(self, point):
      radius = random.randint(25, 45)
      return TouchCircleNode(radius, position=point)
      
    def create_box_shape(self, point):
      width = random.randint(42, 80)
      height = random.randint(42, 80)
      node = BoxNode((width, height), position=point)
      return node
      
    def get_points(self):
      r = random.randint(40, 80)
      magnitude = random.randint(
        int(.3*r), int(.7*r))
        
      points = []
      for a in range(0, 340, 20):
        magnitude = max(
          min(
            magnitude + random.randint(
              int(-.2*r), int(.2*r)), 
            r),
          .2*r)
        point = vector.Vector(magnitude, 0)
        point.degrees = a
        points.append(tuple(point))
      points.append(points[0])
      return points
      
    def create_smooth_shape(self, position):
      points = self.get_points()
      return PointsNode(points, smooth=True, position=position)
      
    def create_polygon_shape(self, position):
      points = self.get_points()
      p = ui.Path()
      for i, point in enumerate(points):
        if i == 0:
          p.move_to(*point)
        else:
          p.line_to(*point)
      p.close()
      return PathNode(path=p, position=position)
  
    def create_sprite_node(self, point):
      return SpriteNode(image=ui.Image('spc:EnemyBlue2'), position=point)

  '''
  scene = TestScene(
    background_color='green',
    gravity=(0,0),
    physics_debug=True)
  scene.view.present(hide_title_bar=True)
  '''
  
  scene = Scene(
    background_color='black',     #1
    physics=SpacePhysics)         #2
    
  class SpaceRock(SpriteNode):    #3
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
      self.angular_velocity = random.random()*4-2
      self.touch_enabled = True   #4
      
    def touch_ended(self, touch): #4
      self.velocity = (
        random.randint(-100, 100),
        random.randint(-100, 100)
      )
    
  ship = SpriteNode(
    image=ui.Image('spc:EnemyBlue2'), 
    position=(150,600),
    velocity=(0, -100),          #5
    parent=scene)
    
  rock = SpaceRock(
    image=ui.Image('spc:MeteorGrayBig3'), 
    position=(170,100),
    velocity=(0,100),
    parent=scene)
    
  scene.camera = CameraNode(parent=scene)
  scene.camera.add_constraint(
    Constraint.distance_to_node(
      ship,
      Range.constant(0))
  )
    
  scene.view.present()
  
  '''
  @script
  def animate(node):
    show(ship1)
    show(ship2)
    yield 1.0
    ship1.velocity = (100,0)
    ship2.velocity = (-100,0)
  '''
    
  #animate(scene)
