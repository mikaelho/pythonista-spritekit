import random, importlib, math, functools, uuid, types, ctypes, itertools

import ui
from objc_util import *
from objc_util import ObjCInstanceMethodProxy
from scene import Point, Rect, Size
import list_callback

import pygestures
from scripter import *

from util import *

class Node:
  
  collision_groups = []
  contact_groups = []
  field_groups = []
  
  default_physics = None
  texture_creation_view = SKView.alloc().init()
  
  def __init__(self, **kwargs):
    self._parent = None
    self._children = []
    self._constraints = list_callback.NotifyList(callback=self._constraint_update)
    if not hasattr(self, 'node'):
      self.node = SKNode.alloc().init()
    self.node.py_node = self
    
    self.paused = False
    self.speed = 1.0
    
    if (self.default_physics is not None and
        self.body is not None and
        not isinstance(self,
          (Scene, CameraNode, FieldNode))):
      for key in dir(self.default_physics()):
        if not key.startswith('_'):
          setattr(self, key, getattr(self.default_physics, key))
    
    name = kwargs.pop('name', None)
    if name is not None:
      self.name = name
      
    self._process_body_bitmasks()
    self._process_field_bitmasks()
    
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
  
  def _process_body_bitmasks(self):
    if self.body == None: return
    if len(self.collision_groups) + len(self.contact_groups) == 0: return

    self.category_bitmask = 0
    self.collision_bitmask = 0

    for i, group in enumerate(self.collision_groups):
      mask = 1 << i
      
      these = [group[0]] if type(group[0]) == str  else group[0]
      those = these if len(group) == 1 else ([group[1]] if type(group[1]) == str  else group[1])
      
      if self.name in these:
        self.collision_bitmask |= mask
      if self.name in those:
        self.category_bitmask |= mask

    for i, group in enumerate(self.contact_groups):
      mask = 1 << (i+len(self.collision_groups))
      
      these = [group[0]] if type(group[0]) == str  else group[0]
      those = these if len(group) == 1 else ([group[1]] if type(group[1]) == str  else group[1])
      
      if self.name in these:
        self.contact_bitmask |= mask
      if self.name in those:
        self.category_bitmask |= mask
  
  def _process_field_bitmasks(self):
    if len(self.field_groups) == 0:
      return
      
    if type(self) is FieldNode or self.body is not None:
      for i, group in enumerate(self.field_groups):
        mask = 1 << i
        
        these = [group[0]] if type(group[0]) == str  else group[0]
        those = [group[1]] if type(group[1]) == str  else group[1]
        
        if self.name in these:
          if self.category_bitmask == 0xFFFFFFFF:
            self.category_bitmask = 0
          self.category_bitmask |= mask
        if self.name in those:
          if self.field_bitmask == 0xFFFFFFFF:
            self.field_bitmask = 0
          self.field_bitmask |= mask
  
  @prop
  def constraints(self, *args):
    if args:
      value = args[0]
      self._constraints = list_callback.NotifyList(callback=self._constraint_update)
      for c in value:
        self._constraints.append(c)
    else:
      return self._constraints

  def add_constraint(self, constraint):
    self.constraints.append(constraint)
    
  def _constraint_update(self):
    sk_constraints = [
      c.constraint for c in self.constraints]
    self.node.setConstraints_(sk_constraints)
      
  def run_action(self, action, key=None):
    if key is None:
      key = str(uuid.uuid4())
    action = Action.check(action)
    self.node.runAction_withKey_(action, key)
    return key
    
  def stop_actions(self, key=None):
    if key is None:
      self.node.removeAllActions()
    else:
      self.node.removeActionForKey_(key)
      
  def convert_point_to(self, point, node):
    return cg_to_py(
      self.node.convertPoint_toNode_(
        py_to_cg(point), node.node))
    
  def convert_point_from(self, point, node):
    return cg_to_py(
      self.node.convertPoint_fromNode_(
        py_to_cg(point), node.node))
        
  def convert_rect_to(self, rect, node):
    x, y = self.convert_point_to((rect.x, rect.y), node)
    x2, y2 = self.convert_point_to((rect.x+rect.w, rect.y+rect.h), node)
    return Rect(x, y, x2-x, y2-y)
    
  def convert_rect_from(self, rect, node):
    x, y = self.convert_point_from((rect.x, rect.y), node)
    x2, y2 = self.convert_point_from((rect.x+rect.w, rect.y+rect.h), node)
    return Rect(x, y, x2-x, y2-y)
      
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
      
  def as_texture(self):
    assert hasattr(self, 'node') and self.node is not None
    return self.texture_creation_view.textureFromNode_(self.node)
    
  def apply_impulse(self, impulse):
    self.body.applyImpulse_(impulse)
  
  def apply_angular_impulse(self, impulse):
    self.body.applyAngularImpulse_(impulse)
  
  def apply_force(self, vector):
    self.body.applyForce_(CGPoint(*vector))
  
  def apply_torque(self, torque):
    self.body.applyTorque_(torque)
    
  def __getitem__(self, key):
    node = self.node.childNodeWithName_(key)
    return None if node is None else ObjCInstance(node).py_node
  
  affected_by_gravity = physics_relay('affectedByGravity')   
  allows_rotation = physics_relay('allowsRotation')
  alpha = node_relay('alpha')
  anchor_point = node_convert('anchorPoint')
  area = physics_relay_readonly('area')
  angular_damping = physics_relay('angularDamping')
  angular_velocity = physics_relay('angularVelocity')
  background_color = fill_color = node_color('fillColor')
  bbox = node_convert('calculateAccumulatedFrame') 
  bullet_physics = physics_relay('usesPreciseCollisionDetection')
  category_bitmask = physics_relay('categoryBitMask')
  charge = physics_relay('charge')
  contact_bitmask = physics_relay('contactTestBitMask')
  collision_bitmask = physics_relay('collisionBitMask')
  density = physics_relay('density')
  dynamic = physics_relay('dynamic')
  field_bitmask = physics_relay('fieldBitMask')
  frame = node_convert('frame')
  friction = physics_relay('friction')
  hidden = node_relay('hidden')
  linear_damping = physics_relay('linearDamping')
  mass = physics_relay('mass')
  name = node_str('name')
  body = node_relay('physicsBody')
  pinned = physics_relay('pinned')
  position = node_convert('position')
  resting = physics_relay_readonly('isResting')
  restitution = physics_relay('restitution')
  
  @prop
  def rotation(self, *args):
    if args:
      value = args[0]
      if 'rotation_offset' in dir(self):
        value += self.rotation_offset
      self.node.setZRotation_(value)
    else:
      value = self.node.zRotation()
      if 'rotation_offset' in dir(self):
        value -= self.rotation_offset
      return value
  
  #rotation = node_relay('zRotation')
  scale_x = node_relay('xScale')
  scale_y = node_relay('yScale')
  size = node_convert('size')
  total_frame = node_convert('calculateAccumulatedFrame')
  touch_enabled = node_relay('userInteractionEnabled')
  velocity = physics_vector('velocity')
  z_position = node_relay('zPosition')

  def needs_body(self, kwargs):
    return not kwargs.get('no_body', False)


class ShapeProperties:
    
  antialiased = node_relay('antialiased')
      
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
  line_color = node_color('strokeColor')
  line_width = node_relay('lineWidth')
  line_length = node_relay('lineLength')
  

class ShapeNode(Node, ShapeProperties):
  
  def __init__(self, path_or_points, smooth=False, hull=False, **kwargs):
    self._path = None
    self.smooth = smooth
    self.hull = hull
    self.create_body = self.needs_body(kwargs)
    path = self.get_path(path_or_points)
    self._path = path
    if self.hull:
      self.node = TouchShapeNode.shapeNodeWithPath_(path.objc_instance.CGPath())
    else:
      self.node = TouchShapeNode.shapeNodeWithPath_centered_(path.objc_instance.CGPath(), True)
    self._create_body(path_or_points)
    super().__init__(**kwargs)
    if not self.hull:
      x,y,w,h = path.bounds
      self.position += (w/2+x,h/2+y)
    
  def get_path(self, path_or_points, smooth=False):
    path_given = type(path_or_points) == ui.Path
    if self.smooth:
      path = ShapeNode.smooth(path_or_points)
    elif type(path_or_points) != ui.Path:
      path = ShapeNode.path_from_points(path_or_points)
    else:
      path = path_or_points
    return path
    
  def _create_body(self, path_or_points):
    if not self.create_body: return 
    if self.hull:
      points = ShapeNode.points_from_path(path_or_points) if type(path_or_points) == ui.Path else path_or_points
      hull_path = ShapeNode.path_from_points(
        ShapeNode.hull(points), 
        start_with_move=False
      )
      cgpath = hull_path.objc_instance.CGPath()
      physics = SKPhysicsBody.bodyWithPolygonFromPath_(cgpath)
      self.node.setPhysicsBody_(physics)
    else:
      texture = self.as_texture()
      physics = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
      self.node.setPhysicsBody_(physics)
    
  def update_path(self, path_or_points, smooth=False):
    path = self.get_path(path_or_points, smooth)
    self.node.setPath_(path.objc_instance.CGPath())
    self._create_body()
    
  @prop
  def path(self, *args):
    if args:
      path_or_points = args[0]
      path = self.get_path(path_or_points, self.smooth)
      self.node.setPath_(path.objc_instance.CGPath())
      self._create_body(path_or_points)
      self._path = path
    else:
      return self._path
      
  def _path_setup(self, path_or_points):
    path_given = type(path_or_points) == ui.Path
    if self.smooth:
      path = ShapeNode.smooth(path_or_points)
    elif not path_given:
      path = ShapeNode.path_from_points(path_or_points)
    else:
      path = path_or_points
    if self.hull:
      self.node = TouchShapeNode.shapeNodeWithPath_(path.objc_instance.CGPath())
      points = ShapeNode.points_from_path(path_or_points) if path_given else path_or_points
      hull_path = ShapeNode.path_from_points(
        ShapeNode.hull(points), 
        start_with_move=False
      )
      if self.create_body:
        cgpath = hull_path.objc_instance.CGPath()
        physics = SKPhysicsBody.bodyWithPolygonFromPath_(cgpath)
        self.node.setPhysicsBody_(physics)
    else:
      self.node = TouchShapeNode.shapeNodeWithPath_centered_(path.objc_instance.CGPath(), True)
      if self.create_body:
        texture = SKView.alloc().init().textureFromNode_(self.node)
        physics = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
        self.node.setPhysicsBody_(physics)
    #super().__init__(**kwargs)
    if not self.hull:
      x,y,w,h = path.bounds
      self.position += (w/2+x,h/2+y)
    
  @classmethod
  def points(cls, points, smooth=False, hull=True, **kwargs):
    path = ShapeNode.path_from_points(points, smooth)
    hull_path = ShapeNode.path_from_points(
      ShapeNode.hull(points), 
      start_with_move=False
    ) if hull else None
    return ShapeNode(path, hull_path, **kwargs)
    
    
  @classmethod
  def path_from_points(cls, points, smooth=False, start_with_move=True):
    assert len(points) > 1
    if smooth:
      #return ShapeNode.quadcurve(points)
      
      return ShapeNode.smooth(points)
    else:
      path = ui.Path()
      if start_with_move:
        path.move_to(*points[0])
      else:
        path.line_to(*points[0])
      for point in points:
        path.line_to(*point)
      if not start_with_move:
        path.line_to(*points[0])
      return path
    
  @classmethod
  def smooth(cls, path_or_points):
    points = ShapeNode.points_from_path(path_or_points) if type(path_or_points) == ui.Path else path_or_points
    cg_points = [ py_to_cg(point) for point in points ]
    cg_points_array = (CGPoint * len(cg_points))(*cg_points)
    node = SKShapeNode.shapeNodeWithSplinePoints_count_(cg_points_array, len(cg_points), restype=c_void_p, argtypes=[POINTER(CGPoint), c_ulong])
    descr = str(ObjCInstance(node.path()))
    path = ui.Path()
    for line in descr.splitlines():
      parts = line.split()
      if len(parts) > 2:
        if parts[0] == 'moveto':
          path.move_to(*eval(
            parts[1]+parts[2]))
        elif parts[0] == 'curveto':
          path.add_curve(
            *eval(parts[5]+parts[6]),
            *eval(parts[1]+parts[2]),
            *eval(parts[3]+parts[4]),
          )
    return path
    
  @classmethod
  def points_from_path(cls, path):
    cgpath = ObjCInstance(path.objc_instance.CGPath())
    descr = str(cgpath)
    points = []
    prev_moveto = None
    for line in descr.splitlines():
      parts = line.split()
      if len(parts) > 2:
        oper = parts[0]
        if oper == 'moveto':
          prev_moveto = eval(
            parts[1]+parts[2])
        elif prev_moveto is not None:
          points.append(Point(*prev_moveto))
          prev_moveto = None
        if oper == 'lineto':
          points.append(Point(*eval(parts[1]+parts[2])))
        elif oper == 'curveto':
          points.append(Point(*eval(parts[5]+parts[6])))
    return points
    
  @classmethod
  def hull(cls, points):
    '''
    Returns points on convex hull in CCW order according to Graham's scan algorithm. 
    By Tom Switzer <thomas.switzer@gmail.com>.
    '''
    TURN_LEFT, TURN_RIGHT, TURN_NONE = (1, -1, 0)

    def cmp(a, b):
      return (a > b) - (a < b)

    def turn(p, q, r):
      return cmp((q[0] - p[0])*(r[1] - p[1]) - (r[0] - p[0])*(q[1] - p[1]), 0)

    def _keep_left(hull, r):
      while len(hull) > 1 and turn(hull[-2], hull[-1], r) == TURN_RIGHT:
      #while len(hull) > 1 and turn(hull[-2], hull[-1], r) != TURN_LEFT:
        hull.pop()
      if not len(hull) or hull[-1] != r:
        hull.append(r)
      return hull

    points = sorted(points)
    l = functools.reduce(_keep_left, points, [])
    u = functools.reduce(_keep_left, reversed(points), [])
    return l.extend(u[i] for i in range(1, len(u) - 1)) or l

  
class BoxNode(Node, ShapeProperties):
  
  def __init__(self, size=(100,100), centered=True, **kwargs):    

    if centered:
      size = py_to_cg(Size(*size))
      self.node = TouchShapeNode.shapeNodeWithRectOfSize_(size)
    else:
      rect = py_to_cg(Rect(*size))
      self.node = TouchShapeNode.shapeNodeWithRect_(rect)
    
    if self.needs_body(kwargs):
      self.node.physicsBody = SKPhysicsBody.bodyWithRectangleOfSize_(size)
    
    super().__init__(**kwargs)


class CircleNode(Node, ShapeProperties):
  
  def __init__(self, radius=50, **kwargs):
    #self.node = None
    #r = self._radius = radius
    
    self.node = TouchShapeNode.shapeNodeWithCircleOfRadius_(radius)
    if self.needs_body(kwargs):
      self.body = SKPhysicsBody.bodyWithCircleOfRadius_(radius)
    
    super().__init__(**kwargs)
      

class PointsNode(Node):
  
  def __init__(self, points, smooth=False, **kwargs):
    cg_points = [ py_to_cg(point) for point in points ]

    cg_points_array = (CGPoint * len(cg_points))(*cg_points)
    
    if smooth:
      self.node = SKShapeNode.shapeNodeWithSplinePoints_count_(cg_points_array, len(cg_points), restype=c_void_p, argtypes=[POINTER(CGPoint), c_ulong])

    else:
      self.node = SKShapeNode.shapeNodeWithPoints_count_(cg_points_array, len(cg_points), restype=c_void_p, argtypes=[POINTER(CGPoint), c_ulong])

    self.anchor_point = (0,0)

    texture = SKView.alloc().init().textureFromNode_(self.node)
    self.node = TouchSpriteNode.spriteNodeWithTexture_(texture)
    physics = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
    self.node.setPhysicsBody_(physics)
    
    print(self.anchor_point)
    
    super().__init__(**kwargs)


class EffectNode(Node):
  
  def __init__(self, **kwargs):
    self.node = SKEffectNode.alloc().init()
    super().__init__(**kwargs)
  
  cache_content = node_relay('shouldRasterize')
  

class CameraNode(Node):
  
  def __init__(self, **kwargs):
    self.node = SKCameraNode.alloc().init()
    self.corners = None
    self.layers = list_callback.NotifyList(callback=self._layers_update)
    super().__init__(**kwargs)
    self.prev_position = self.position
    
  def resize(self):
    w,h = self.scene.size
    for node in self.children:
      if hasattr(node, 'camera_anchor'):
        anchor = node.camera_anchor
        x = anchor.anchor_point.x * w - w/2 + anchor.offset.x
        y = anchor.anchor_point.y * h - h/2 + anchor.offset.y
        node.position = (x, y)
    
  def visible(self, node):
    return self.node.containsNode_(node.node)
    
  def visible_nodes():
    visible = set()
    for sk_node in self.node.containedNodeSet_():
      visible.add(sk_node.py_node)
    return visible
    
  def update_layers(self):
    delta = self.position - self.prev_position
    self.prev_position = self.position
    if abs(delta) > 0 and len(self.layers):
      self.delta_pan(delta)
    
  def _layers_update(self):
    for i, layer in enumerate(self.layers):
      layer.z_position = -(i+1)*10
      layer.parent = self
      layer.layout()
    self.delta_pan()
    
  def delta_pan(self, delta=Point(0,0)):
    delta = Point(*delta)
    for layer in self.layers:
      layer.delta_pan(delta)
  
  def delta_scale(self, delta=1):
    for layer in self.layers:
      layer.delta_scale(delta)
  
  
class Layer(EffectNode):
  
  def __init__(self, tile, pan_factor=1, scale_factor=1, **kwargs):
    super().__init__(**kwargs)
    self.cache_content = True
    self.tile = tile
    if type(pan_factor) in (tuple, list):
      pan_factor = Point(*pan_factor)
    self.pan_factor = pan_factor
    self.scale_factor = scale_factor
  
  def delta_pan(self, delta):
    delta = delta * self.pan_factor
    x, y = self.position
    x = (x - delta.x) % self.tile.size.x
    y = (y - delta.y) % self.tile.size.y
    self.position = (x,y)
    self.layout()
    
  def delta_scale(self, delta):
    self.scale *= (delta * self.scale_factor)
    self.layout()
    
  def layout(self):
    cx, cy, cw, ch = self.total_frame
    tw, th = self.tile.size
    cols, rows = int(cw/tw), int(ch/th)
    x, y, w, h = self.scene.bounds
    if w > cw/3 or h > ch/3:
      h_count = int(3 * math.ceil(w/tw))
      v_count = int(3 * math.ceil(h/th))
      h_end = math.floor(h_count/2)
      h_start = -(h_count - h_end)
      v_end = math.floor(v_count/2)
      v_start = -(v_count - v_end)
      for col in range(h_start, h_end):
        for row in range(v_start, v_end):
          if self[f'cr{row}{col}'] is None:
            s = SpriteNode(self.tile,
              name=f'cr{row}{col}',
              no_body=True,
              position=(col*tw, row*th),
              parent=self)
      point = Point(
        math.floor(h_count/2)/h_count,
        math.floor(v_count/2)/v_count
      )
      self.anchor_point = point
      self.position = (0,0)
      #print(self.anchor_point)
      

class Anchor:
  
  def __init__(self, anchor_point, offset):
    self.anchor_point = ui.Point(*anchor_point)
    self.offset = ui.Point(*offset)
    
    
class EdgePathNode(Node):
  
  def __init__(self, path, **kwargs):
    assert type(path) == ui.Path
    super().__init__(**kwargs)
    cgpath = path.objc_instance.CGPath()
    physics = SKPhysicsBody.bodyWithEdgeChainFromPath_(cgpath)
    if physics is None:
      raise RuntimeError('Could not create the edge. Did you start the path with move_to? Must start with a line from (0,0).')
    self.body = physics
    
    
class SpriteNode(Node):
  
  def __init__(self, image=None,  alpha_threshold=None, **kwargs):
    texture = None
    if image is not None:
      image_texture = Texture(image)
      texture = image_texture.texture
    '''
    if type(image) == ui.Image:
      texture = SKTexture.textureWithImage_(ObjCInstance(image))
    '''
    self.node = TouchSpriteNode.spriteNodeWithTexture_(texture)
    if self.needs_body(kwargs):
      if alpha_threshold is None:
        self.node.physicsBody = SKPhysicsBody.bodyWithTexture_size_(texture, texture.size())
      else:
        self.node.physicsBody = SKPhysicsBody.bodyWithTexture_alphaThreshold_size_(texture, alpha_threshold, texture.size())
    super().__init__(**kwargs)
    
  color = node_color('color')
  color_blend = node_relay('colorBlendFactor')
  lighting_bitmask = node_relay('lightingBitMask')
  shadowed_bitmask = node_relay('shadowedBitMask')
  shadow_cast_bitmask = node_relay('shadowCastBitMask')
    
  texture = node_texture('texture')
  normal_texture = node_texture('normalTexture')

  @prop
  def warp(self, *args):
    if args:
      value = args[0]
      self.node.setWarpGeometry_(value.geometry)
    else:
      return WarpGrid(geometry=self.node.warpGeometry())


class float2(Structure):
  _fields_ = [('x',c_float),('y',c_float)]
    

class WarpGrid:
  
  def __init__(self, cols=0, rows=0, geometry=None):
    if geometry is not None:
      self.geometry = geometry
    elif cols > 0 and rows > 0:
      self.geometry = SKWarpGeometryGrid.gridWithColumns_rows_(cols-1, rows-1)
    else:
      self.geometry = SKWarpGeometryGrid.grid()
    
  def set_sources(self, positions):
    assert len(positions) == self.vertices
    src_pos = (float2*len(positions))(*positions)
    self.geometry = warp.gridByReplacingSourcePositions_(
      byref(dest_pos),
      restype=c_void_p, argtypes=[c_void_p])
    return self
    
  def set_destinations(self, positions):
    assert len(positions) == self.vertices
    dest_pos = (float2*len(positions))(*positions)
    self.geometry = self.geometry.gridByReplacingDestPositions_(
      byref(dest_pos),
      restype=c_void_p, argtypes=[c_void_p])
    return self
    
  @property
  def columns(self):
    return self.geometry.numberOfColumns()+1
    
  @property
  def rows(self):
    return self.geometry.numberOfRows()+1
    
  @property
  def vertices(self):
    return self.geometry.vertexCount()
    
  @property
  def sources(self):
    return [d for d in ctypes.cast(
      self.geometry.sourcePositions(), 
      POINTER(float2*self.vertices)).contents]
      
  @property
  def destinations(self):
    return [d for d in ctypes.cast(
      self.geometry.destPositions(), 
      POINTER(float2*self.vertices)).contents]
  
  @classmethod    
  def tuples(cls, positions):
    return [(f.x, f.y) for f in positions]
    
  def set_spiral(self, max_rotation=0):
    V = Vector
    origin = Vector(0.5,0.5)
    l = WarpGrid.tuples(self.sources)
    list_2d = [l[i:i+self.rows] for i in range(0, len(l), self.rows)]
    for row in range(self.rows):
      for col in range(self.columns):
        current = Vector(list_2d[row][col])
        pointer = current-origin
        distance_factor = pointer.magnitude/0.5
        pointer.radians += distance_factor * max_rotation
        list_2d[row][col] = tuple(origin+pointer)
    return self.set_destinations(list(itertools.chain.from_iterable(list_2d)))
        
  def soften(self, variance=0.1):
    V = Vector
    origin = Vector(0.5,0.5)
    l = WarpGrid.tuples(self.sources)
    list_2d = [l[i:i+self.rows] for i in range(0, len(l), self.rows)]
    for row in range(self.rows):
      for col in range(self.columns):
        current = Vector(list_2d[row][col])
        pointer = current-origin
        original = pointer.magnitude
        pointer.magnitude = original + random.random()*original*variance-0.5*variance
        list_2d[row][col] = tuple(origin+pointer)
    return self.set_destinations(list(itertools.chain.from_iterable(list_2d)))
        

class LabelNode(Node):
  
  def __init__(self, text, **kwargs):
    assert type(text) == str
    self.node = SKLabelNode.labelNodeWithText_(text)      
    super().__init__(**kwargs)
    
  ALIGN_CENTER = 0
  ALIGN_LEFT = 1
  ALIGN_RIGHT = 2
    
  ALIGN_BASELINE = 0
  ALIGN_MIDDLE = 1
  ALIGN_TOP = 2
  ALIGN_BOTTOM = 3
    
  text = node_str('text')
  font_color = node_color('fontColor')
  font_name = node_relay('fontName')
  font_size = node_relay('fontSize')
  alignment = node_relay('horizontalAlignmentMode')
  vertical_alignment = node_relay('verticalAlignmentMode')
  line_break_mode = node_relay('lineBreakMode')
  max_width = node_relay('preferredMaxLayoutWidth')
  number_of_lines = node_relay('numberOfLines')
  
  @prop
  def font(self, *args):
    if args:
      value = args[0]
      self.font_name = value[0]
      self.font_size = value[1]
    else:
      return (self.font_name, self.font_size)


class LightNode(Node):
  
  def __init__(self, **kwargs):
    self.node = SKLightNode.alloc().init()
    super().__init__(**kwargs)
  
  enabled = node_relay('enabled')
  ambient_color = node_color('ambientColor')
  light_color = node_color('lightColor')
  shadow_color = node_color('shadowColor')
  falloff = node_relay('falloff')
  category_bitmask = node_relay('categoryBitMask')


class Joint:
  
  ''' WARNING: Trying to use joints with shape-type physics body results in an ObjC exception. '''
  
  @classmethod
  def pin(cls, node_a, node_b, anchor):
    j = SKPhysicsJointPin.jointWithBodyA_bodyB_anchor_(
      node_a.body, node_b.body, 
      py_to_cg(anchor))
    node_a.scene.node.physicsWorld().addJoint_(j)
    
  @classmethod
  def spring(cls, node_a, node_b, anchor_a, anchor_b, damping=0, frequency=0):
    j = SKPhysicsJointSpring.jointWithBodyA_bodyB_anchorA_anchorB_(
      node_a.body, node_b.body, 
      py_to_cg(anchor_a), py_to_cg(anchor_b))
    j.setDamping_(damping)
    j.setFrequency_(frequency)
    node_a.scene.node.physicsWorld().addJoint_(j)
    

class FieldNode(Node):
  
  def __init__(self, fieldnode, **kwargs):
    self.node = fieldnode
    super().__init__(**kwargs)
  
  @classmethod
  def drag(cls, **kwargs):
    return FieldNode(SKFieldNode.dragField(), **kwargs)
    
  @classmethod
  def electric(cls, **kwargs):
    return FieldNode(SKFieldNode.electricField(), **kwargs)
    
  @classmethod
  def linear_gravity(cls, gravity_vector, **kwargs):
    return FieldNode(
      SKFieldNode.linearGravityFieldWithVector_(py_to_cg(gravity_vector)), **kwargs)
    
  @classmethod
  def magnetic(cls, **kwargs):
    return FieldNode(SKFieldNode.magneticField(), **kwargs)
    
  @classmethod
  def noise(cls, smoothness, animation_speed, **kwargs):
    return FieldNode(
      SKFieldNode.noiseFieldWithSmoothness_animationSpeed_(
        smoothness,
        animation_speed), **kwargs)
        
  @classmethod
  def radial_gravity(cls, **kwargs):
    return FieldNode(
      SKFieldNode.radialGravityField(), **kwargs)
      
  @classmethod
  def spring(cls, **kwargs):
    return FieldNode(
      SKFieldNode.springField(), **kwargs)
      
  @classmethod
  def turbulence(cls, smoothness, animation_speed, **kwargs):
    return FieldNode(
      SKFieldNode.turbulenceFieldWithSmoothness_animationSpeed_(
        smoothness,
        animation_speed), **kwargs)
        
  @classmethod
  def velocity_texture(cls, texture, **kwargs):
    assert type(texture) == Texture
    return FieldNode(
      SKFieldNode.velocityFieldWithTexture_(texture.texture), **kwargs)
        
  @classmethod
  def velocity_vector(cls, vector, **kwargs):
    return FieldNode(
      SKFieldNode.velocityFieldWithVector_(py_to_cg(vector)), **kwargs)
      
  @classmethod
  def vortex(cls, **kwargs):
    return FieldNode(SKFieldNode.vortexField(), **kwargs)
    
  category_bitmask = node_relay('categoryBitMask')
  enabled = node_relay('enabled')
  exclusive = node_relay('exclusive')
  falloff = node_relay('falloff')
  minimum_radius = node_relay('minimumRadius')
  strength = node_relay('strength')
  
  @prop
  def region(self, *args):
    if args:
      value = args[0]
      assert type(value) == Region
      self.node.setRegion_(value.region)
    else:
      return Region(self.node.region)
  
  
class Background(Node):
  ''' Manages background layers. '''
  
  def __init__(self, tiles=None, **kwargs):
    super().__init__(**kwargs)
    
  
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
    
    
class EmitterNode(Node):
  
  def __init__(self, **kwargs):
    self.node = SKEmitterNode.alloc().init()
    super().__init__(**kwargs)
  
  @prop
  def target_node(self, *args):
    if args:
      value = args[0]
      self.node.setTargetNode_(value.node)
    else:
      target = self.node.targetNode()
      if target is None: return None
      else: return target.py_node
  
  emission_angle = node_relay('emissionAngle')
  emission_angle_range = node_relay('emissionAngleRange')
  emission_distance = node_relay('emissionDistance')
  emission_distance_range = node_range('emissionDistanceRange')
  num_particles_to_emit = node_relay('numParticlesToEmit')
  particle_action = node_relay('particleAction')
  particle_alpha = node_relay('particleAlpha')
  particle_alpha_range = node_relay('particleAlphaRange')
  particle_alpha_speed = node_relay('particleAlphaSpeed')
  particle_birth_rate = node_relay('particleBirthRate')
  particle_blend_mode = node_relay('particleBlendMode')
  particle_color = node_color('particleColor')
  particle_color_alpha_range = node_range('particleColorAlphaRange')
  particle_color_alpha_speed = node_relay('particleColorAlphaSpeed')
  particle_cplor_blend_factor = node_relay('particleColorBlendFactor')
  particle_color_blend_factor_range = node_relay('particleColorBlendFactorRange')
  particle_color_blend_factor_speed = node_relay('particleColorBlendFactorSpeed')
  particle_color_blue_range = node_range('particleColorBlueRange')
  particle_color_blue_speed = node_relay('particleColorBlueSpeed')
  particle_color_green_range = node_range('particleColorGreenRange')
  particle_color_green_speed = node_relay('particleColorGreenSpeed')
  particle_color_red_range = node_range('particleColorRedRange')
  particle_color_red_speed = node_relay('particleColorRedSpeed')
  particle_density = node_relay('particleDensity')
  particle_life_time = node_relay('particleLifetime')
  particle_life_time_range = node_range('particleLifetimeRange')
  particle_position = node_relay('particlePosition')
  particle_position_range = node_range('particlePositionRange')
  particle_render_order = node_relay('particleRenderOrder')
  particle_rotation = node_relay('particleRotation')
  particle_rotation_range = node_range('particleRotationRange')
  particle_rotation_speed = node_relay('particleRotationSpeed')
  particle_scale = node_relay('particleScale')
  particle_scale_range = node_range('particleScaleRange')
  particle_scale_speed = node_relay('particleScaleSpeed')
  particle_size = node_convert('particleSize')
  particle_speed = node_relay('particleSpeed')
  particle_speed_range = node_range('particleSpeedRange')
  particle_texture = node_relay('particleTexture')
  particle_z_position = node_relay('particleZPosition')
  particle_z_position_range = node_range('particleZPositionRange')
  particle_z_position_speed = node_relay('particleZPositionSpeed')


def _action(objc_func_name):
  @classmethod
  def _f(cls, duration=0.5, timing=None):
    a = getattr(SKAction, objc_func_name)(duration)
    if timing is not None:
      a.setTimingMode_(timing)
    return a
  return _f
  
def _action_scalar(objc_func_name):
  @classmethod
  def _f(cls, scalar, duration=0.5, timing=None):
    a = getattr(SKAction, objc_func_name)(scalar, duration)
    if timing is not None:
      a.setTimingMode_(timing)
    return a
  return _f
  
def _action_point(objc_func_name):
  @classmethod
  def _f(cls, point, duration=0.5, timing=None):
    a = getattr(SKAction, objc_func_name)(
      py_to_cg(point), duration)
    if timing is not None:
      a.setTimingMode_(timing)
    return a
  return _f
  
def _action_vector(objc_func_name):
  @classmethod
  def _f(cls, vector, duration=0.5, timing=None):
    cgvector = CGVector(dx=vector[0], dy=vector[1])
    a = getattr(SKAction, objc_func_name)(
      cgvector, duration)
    if timing is not None:
      a.setTimingMode_(timing)
    return a
  return _f
  
def _action_vector_point(objc_func_name):
  @classmethod
  def _f(cls, vector, point, duration=0.5, timing=None):
    cgvector = CGVector(*vector)
    a = getattr(SKAction, objc_func_name)(
      vector,
      py_to_cg(point),
      duration)
    if timing is not None:
      a.setTimingMode_(timing)
    return a
  return _f
  
def _action_path(objc_func_name):
  @classmethod
  def _f(cls, path, duration=0.5, timing=None):
    assert type(path) == ui.Path
    cgpath = path.objc_instance.CGPath()
    a = getattr(SKAction, objc_func_name)(cgpath, duration)
    if timing is not None:
      a.setTimingMode_(timing)
    return a
  return _f
  
class Action:
  
  LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT = range(4)
  
  @classmethod
  def group(cls, actions):
    actions = [
      cls.check(action)
      for action in actions
    ]
    return SKAction.group_(actions)
    
  @classmethod
  def sequence(cls, actions):
    actions = [
      cls.check(action)
      for action in actions
    ]
    return SKAction.sequence_(actions)
  
  @classmethod
  def repeat(cls, action, count):
    action = cls.check(action)
    return SKAction.repeatAction_count_(action, count)

  @classmethod
  def forever(cls, action):
    action = cls.check(action)
    return SKAction.repeatActionForever_(action)
  
  @classmethod
  def check(cls, action):
    if type(action) == set:
      return cls.group([a for a in action])
    elif type(action) in (tuple, list):
      return cls.sequence(action)
    else:
      return action
  
  angular_impulse = _action_scalar('applyAngularImpulse_duration_')
  force_at = _action_vector_point('applyForce_atPoint_duration_')
  force = _action_vector('applyForce_duration_')
  impulse_at = _action_vector_point('applyImpulse_atPoint_duration_')
  impulse = _action_vector('applyImpulse_duration_')
  torque = _action_scalar('applyTorque_duration_')
  charge_by = _action_scalar('changeChargeBy_duration_'
  )
  charge_to = _action_scalar('changeChargeTo_duration_')
  mass_by = _action_scalar('changeMassBy_duration_')
  mass_to = _action_scalar('changeMassTo_duration_')
  obstruction_by = _action_scalar('changeObstructionBy_duration_')
  obstruction_to = _action_scalar('changeObstructionTo_duration_')
  occlusion_by = _action_scalar('changeOcclusionBy_duration_')
  occlusion_to = _action_scalar('changeOcclusionTo_duration_')
  playback_rate_by = _action_scalar('changePlaybackRateBy_duration_')
  playback_rate_to = _action_scalar('changePlaybackRateTo_duration_')
  reverb_by = _action_scalar('changeReverbBy_duration_')
  reverb_to = _action_scalar('changeReverbTo_duration_')
  volume_by = _action_scalar('changeVolumeBy_duration_')
  volume_to = _action_scalar('changeVolumeTo_duration_')
  alpha_by = _action_scalar('fadeAlphaBy_duration_')
  alpha_to = _action_scalar('fadeAlphaTo_duration_')
  fade_in = _action('fadeInWithDuration_')
  fade_out = _action('fadeOutWithDuration_')
  falloff_by = _action_scalar('falloffBy_duration_')
  falloff_to = _action_scalar('falloffTo_duration_')
  follow_path = _action_path('followPath_duration_')
  move_by = _action_vector('moveBy_duration_')
  move_to = _action_point('moveTo_duration_')
  move_to_x = _action_scalar('moveToX_duration_')
  move_to_y = _action_scalar('moveToY_duration_')
  rotate_by = _action_scalar('rotateByAngle_duration_')
  rotate_to = _action_scalar('rotateToAngle_duration_')  
  scale_by = _action_scalar('scaleBy_duration_')
  scale_to = _action_scalar('scaleTo_duration_')
  height_to = _action_scalar('resizeToHeight_duration_')
  width_to = _action_scalar('resizeToWidth_duration_')
  wait = _action('waitForDuration_')
  
  @classmethod
  def warp_to(cls, warp, duration=0.5):
    return SKAction.warpTo_duration_(
      warp.geometry, duration)
      
  @classmethod
  def warps(cls, warps, times=None, restore=False, duration=0.5):
    if times is None:
      times = [
        duration/len(warps)*(i+1)
        for i in range(len(warps))
      ]
    geometries = [w.geometry for w in warps]
    return SKAction.animateWithWarps_times_restore_(geometries, times, restore)
  
'''

TODO:
  
animateWithNormalTextures_timePerFrame_
animateWithNormalTextures_timePerFrame_resize_restore_
animateWithTextures_timePerFrame_
animateWithTextures_timePerFrame_resize_restore_

colorizeWithColorBlendFactor_duration_
colorizeWithColor_colorBlendFactor_duration_
convertAction_toDuration_
followPath_asOffset_orientToPath_duration_
followPath_asOffset_orientToPath_speed_
followPath_speed_

moveByX_y_duration_
pause
play
playSoundFileNamed_
playSoundFileNamed_atPosition_waitForCompletion_
playSoundFileNamed_waitForCompletion_
reachToNode_rootNode_duration_
reachToNode_rootNode_velocity_
reachTo_rootNode_duration_
reachTo_rootNode_velocity_
recursivePathsForResourcesOfType_inDirectory_
resizeByWidth_height_duration_
resizeToHeight_duration_
resizeToWidth_duration_
resizeToWidth_height_duration_
rotateToAngle_duration_shortestUnitArc_
scaleToSize_duration_
scaleXBy_y_duration_
scaleXTo_duration_
scaleXTo_y_duration_
scaleYTo_duration_
setNormalTexture_
setNormalTexture_resize_
setTexture_
setTexture_resize_
speedBy_duration_
speedTo_duration_
stereoPanBy_duration_
stereoPanTo_duration_
stop
strengthBy_duration_
strengthTo_duration_
waitForDuration_withRange_

'''
    
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
      self.constraint.setReferenceNode_(value.node)
    else:
      return self.constraint.referenceNode().py_node
  
  @classmethod
  def distance_to_node(cls, node, distance=Range.constant(0)):
    assert isinstance(node, Node)
    assert type(distance) == Range
    return Constraint(SKConstraint.distance_toNode_(
      distance.range, node.node))
  
  @classmethod
  def distance_to_point(cls, point, distance=Range.constant(0)):
    point = py_to_cg(point)
    assert type(distance) == Range
    return Constraint(SKConstraint.distance_toPoint_(
      distance.range, point))
  
  @classmethod
  def distance_to_point_in_node(cls, point, node, distance=Range.constant(0)):
    point = py_to_cg(point)
    assert isinstance(node, Node)
    assert type(distance) == Range
    return Constraint(SKConstraint.distance_toPoint_inNode_(
      distance.range, point, node.node))
  
  @classmethod
  def orient_to_node(cls, node, offset=Range.constant(0)):
    assert isinstance(node, Node)
    assert type(offset) == Range
    return Constraint(SKConstraint.orientToNode_offset_(
      node.node, offset.range))
      
  @classmethod
  def orient_to_point(cls, point, offset=Range.constant(0)):
    point = py_to_cg(point)
    assert type(offset) == Range
    return Constraint(SKConstraint.orientToPoint_offset_(
      point, offset.range))
      
  @classmethod
  def orient_to_point_in_node(cls, point, node, offset=Range.constant(0)):
    point = py_to_cg(point)
    assert isinstance(node, Node)
    assert type(offset) == Range
    return Constraint(SKConstraint.orientToPoint_inNode_offset_(
      point, node.node, offset.range))
  
  @classmethod
  def position(cls, x_range=Range.constant(0), y_range=Range.constant(0)):
    assert type(x_range) == Range
    assert type(y_range) == Range
    return Constraint(SKConstraint.positionX_Y_(
      x_range.range, y_range.range))
      
  @classmethod
  def position_x(cls, x_range=Range.constant(0)):
    assert type(x_range) == Range
    return Constraint(SKConstraint.positionX_(
      x_range.range))
      
  @classmethod
  def position_y(cls, y_range=Range.constant(0)):
    assert type(y_range) == Range
    return Constraint(SKConstraint.positionY_(
      y_range.range))
      
  @classmethod
  def rotation(cls, range=Range.constant(0)):
    assert type(range) == Range
    return Constraint(SKConstraint.zRotation_(
      range.range))
  
  @classmethod
  def scale(cls, scale_range=Range.constant(1)):
    assert type(scale_range) == Range
    return Constraint(SKConstraint.scaleX_scaleY_(
      scale_range.range, scale_range.range))
      
  @classmethod
  def scale_x(cls, x_range=Range.constant(1)):
    assert type(x_range) == Range
    return Constraint(SKConstraint.scaleX_(
      x_range.range))
      
  @classmethod
  def scale_y(cls, y_range=Range.constant(1)):
    assert type(y_range) == Range
    return Constraint(SKConstraint.scaleY_(
      y_range.range))
    

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
  '''Complicated checks to avoid problems due to scene getting restarted upon resume.'''
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
  objc_scene = ObjCInstance(_self)
  if hasattr(objc_scene, 'py_node'):
    scene = objc_scene.py_node
    if scene.edges:
      v = scene.view
      scene.set_edge_loop(
        0, 0, v.width, v.height)
    if hasattr(scene, 'layout'):
      scene.layout()
    if scene.camera is not None:
      scene.camera.resize()

def didBeginContact_(_self, _cmd, _contact):
  scene = ObjCInstance(_self)
  contact = ObjCInstance(_contact)
  if hasattr(scene, 'py_node'):
    data = types.SimpleNamespace(
      node_a=contact.bodyA().node().py_node,
      node_b=contact.bodyB().node().py_node,
      point=cg_to_py(contact.contactPoint()),
      impulse=contact.collisionImpulse(),
      normal=cg_to_py(contact.contactNormal())
    )
    #node_a = contact.bodyA().node().py_node
    #node_b = contact.bodyB().node().py_node
    
    scene.py_node.contact(data)


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
  
  @on_main_thread
  def __init__(self, physics=None, touchable=False, physics_debug=False, field_debug=False, **kwargs):
    kwargs['physics_debug'] = physics_debug
    kwargs['field_debug'] = field_debug
    self.corners = None
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
      sk_camera = self.node.camera()
      return None if sk_camera is None else  sk_camera.py_node
      
  def contact(self, data):
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
  background_color = node_color('backgroundColor')
  
class TouchScene(Scene):
  
  def __init__(self, can_pan=True, can_pinch=False, can_rotate=False, **kwargs):
    self.can_pan = can_pan
    self.can_pinch = can_pinch
    self.can_rotate = can_rotate
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

  @on_main_thread
  def __init__(self, physics_debug=False, field_debug=False, **kwargs):
    super().__init__(**kwargs)
    rect = CGRect(CGPoint(0, 0),CGSize(self.width, self.height))
    skview = SKView.alloc().initWithFrame_(rect)
    skview.autoresizingMask = 2 + 16 # WH
    #skview.showsNodeCount = True
    if physics_debug:
      skview.showsPhysics = True
    if field_debug:
      skview.showsFields = True
    ObjCInstance(self).addSubview(skview)
    self.skview = skview
    self.multitouch_enabled = True
    self.skview.setMultipleTouchEnabled_(True)

  def will_close(self):
    delattr(self.scene.node, 'py_node')
    self.scene.node.removeAllChildren()
    # Must pause to stop update_
    self.scene.node.paused = True
    self.scene.node.removeFromParent()
    self.skview.removeFromSuperview()
    #self.scene.node.release()
    self.skview.release()
    self.skview = None
    #self.scene.node = None


class TouchView(
  ui.View, pygestures.GestureMixin):
      
  def on_tap(self, g):
    if hasattr(self.scene, 'on_tap'):
      g.location = self.scene.convert_from_view(g.location)
      self.scene.on_tap(g)
    
  def on_pan(self, g):
    if not self.scene.can_pan: return
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
    if not self.scene.can_pinch: return
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
    if not self.scene.can_rotate: return
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
  
class UIPhysics(BasePhysics):
  gravity = (0, 0)
  affected_by_gravity = False
  allows_rotation = False
  bullet_physics = False
  dynamic = True
  friction = 0.2
  linear_damping = 0.2
  restitution = 0.0

@on_main_thread
def run(scene, *args, **kwargs):
  scene.view.present(*args, **kwargs)
  #if hasattr(scene, 'setup'):
  #  scene.setup()


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
      '''
      p = ui.Path()
      for i, point in enumerate(points):
        if i == 0:
          p.move_to(*point)
        else:
          p.line_to(*point)
      '''
      p = PathNode.quadcurve(points)
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
  
  def get_points():
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
    
  def create_polygon_shape(position, smooth=False):
    points = get_points()
    path = ShapeNode.path_from_points(points)
    return ShapeNode(path, smooth=smooth, 
    hull=False, position=position)
  
  def create_circle_shape(point):
    radius = random.randint(25, 45)
    return CircleNode(radius, position=point)
  
  scene = Scene(
    background_color='black',     
    physics=SpacePhysics,
    #physics_debug=True,
  )         
    
  class SpaceRock(SpriteNode):    
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
      self.angular_velocity = random.random()*4-2
      self.touch_enabled = True   #4
      
    def touch_ended(self, touch): #4
      self.velocity = (
        random.randint(-100, 100),
        random.randint(-100, 100)
      )
  
  rock = SpriteNode(
    'spc:MeteorGrayBig3',
    lighting_bitmask=1,
    parent=scene)
    
  rock_too = SpriteNode(
    'spc:MeteorGrayBig3', 
    normal_texture=Texture('spc:MeteorGrayBig3').normal_map(contrast=10),
    lighting_bitmask=1,
    position=(100,200),
    parent=scene,
  )
    
  light = LightNode(
    category_bitmask=1,
    light_color='white',
    falloff=1.2,
    position=(50,100),
    parent=scene
  )
    
  points = get_points()
  path = ShapeNode.path_from_points(points)
  
  ShapeNode(path, position=(100,800),
  fill_color='grey', parent=scene)
    
  ShapeNode(path, position=(250,800),
  smooth=True,
  fill_color='grey', parent=scene)
    
  scene.camera = CameraNode(parent=scene)
  scene.camera.add_constraint(
    Constraint.distance_to_node(
      rock,
      Range.constant(0))
  )
    
  scene.view.present()

