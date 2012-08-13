# Much of this code was not so casually ported from
#
# https://flathead.ornl.gov/repos/TranslationService/trunk/sns-translation-client/sns-translation-core/src/main/java/gov/ornl/sns/translation/geometry/calc/helpers/RectCorners.java
#

import math

TOLERANCE = .0001

class Vector:
    """
    This class encapsulates the concept of a vector in 3D space from
    geometry
    """

    LENGTH = 3

    def __init__(self, x=None, y=None, z=None):
        # set the data
        if y is None and z is None:
            if x is None:
                self.__data = [0.]*Vector.LENGTH
            else:
                try:
                    self.__data = x.__data[:]
                except AttributeError, e:
                    if len(x) != Vector.LENGTH:
                        raise RuntimeError("Expected 3 values, found %d" % len(x))
                    self.__data = x[:Vector.LENGTH]
        else:
            self.__data = [x, y, z]

        # convert the values to floats
        self.__data = [float(num) for num in self.__data]

        # sanity check the numbers
        for num in self.__data:
            if math.isnan(num):
                raise RuntimeError("Encountered NaN")

    x = property(lambda self: self.__data[0])
    y = property(lambda self: self.__data[1])
    z = property(lambda self: self.__data[2])

    def cross(self, other):
        """
        Calculate the cross product of this with another vector.
        """
        result = [0.]*Vector.LENGTH
        result[0] = self.y*other.z - self.z*other.y
        result[1] = self.z*other.x - self.x*other.z
        result[2] = self.x*other.y - self.y*other.x

        return Vector(result)

    def dot(self, other):
        """
        Calculate the dot product of this with another vector.
        """
        result = 0.
        for (a, b) in zip (self.__data, other.__data):
            result += a*b
        return result

    def normalize(self):
        """
        Set the unit length to one
        """
        length = self.length # cache value
        if abs(length) < TOLERANCE:
            raise RuntimeError("Zero vector of zero length")
        if abs(length -1.) < TOLERANCE:
            return self # nothing to do
        self.__data = [it/length for it in self.__data]

        return self

    def __getitem__(self, key):
        return self.__data[key]

    def __eq__(self, other):
        other = Vector(other)
        if not self.x == other.x:
            return False
        if not self.y == other.y:
            return False
        if not self.z == other.z:
            return False
        return True

    def __add__(self, other):
        temp = Vector()
        for i in range(Vector.LENGTH):
            temp.__data[i] = self.__data[i] + other.__data[i]
        return temp

    def __sub__(self, other):
        temp = Vector()
        for i in range(Vector.LENGTH):
            temp.__data[i] = self.__data[i] - other.__data[i]
        return temp

    def __div__(self, other):
        other = float(other) # only allow divide by a scalar
        temp = Vector(self)
        for i in range(Vector.LENGTH):
            temp.__data[i] /= float(other)
        return temp

    def __mul__(self, other):
        other = float(other) # only allow multiply by a scalar
        temp = Vector(self)
        for i in range(Vector.LENGTH):
            temp.__data[i] *= float(other)
        return temp

    def __rmul__(self, other):
        return self * other

    def __repr__(self):
        temp = [str(it) for it in self.__data]
        return "(%s)" % (", ".join(temp))

    def __len__(self):
        return Vector.LENGTH

    length = property(lambda self: math.sqrt(self.dot(self)))

UNIT_X = Vector(1.,0.,0.)
UNIT_Y = Vector(0.,1.,0.)
UNIT_Z = Vector(0.,0.,1.)

def getAngle(y, x, debug=False):
    """
    Returns the angle in radians using atan2.
    """
    if debug:
        print "getAngle(%f, %f)=" % (y, x),
    angle = math.atan2(y, x)
    if angle < 0:
        angle += 2*math.pi
    if debug:
        print math.degrees(angle)
    return angle

class Rectangle:
    NPOINTS = 4
    BOTTOMLEFT = 1
    TOPLEFT = 2
    TOPRIGHT = 3
    BOTTOMRIGHT = 4

    def __init__(self, p1, p2, p3, p4):
        p1 = Vector(p1)
        p2 = Vector(p2)
        p3 = Vector(p3)
        p4 = Vector(p4)

        # Are they 4 edges of a 2D plane arrange so consecutive
        # points with wrap are edges
        d1 = self.__magnitudeSq(p1, p2)
        d2 = self.__magnitudeSq(p1, p3)
        d3 = self.__magnitudeSq(p1, p4)
        if d1 > d2 or d3 > d2:
            if d1 > d2:
                specific = " (d1=|p1-p2|=%f > d2=|p1-p3|=%f)" % (d1, d2)
            if d3 > d2:
                specific = " (d3=|p1-p4|=%f > d2=|p1-p3|=%f)" % (d3, d2)
            raise RuntimeError("The Points are in the incorrect order"+specific)


        # Parallelogram opposite side from p1 to p4 is parallel and 
        # equal lengths.
        left = p2-p1
        right = p4-p3
        if abs(left.length - right.length) > TOLERANCE:
            msg = "Left and right sides are not equal length: " \
                + "left=%f != right=%f (diff=%f)" \
                % (left.length, right.length, abs(left.length-right.length))
            raise RuntimeError(msg)

        top = p2-p3
        bottom = p4-p1
        if abs(top.length - bottom.length) > TOLERANCE:
            msg = "Top and bottom sides are not equal length: "\
                + "top=%f != bottom=%f (diff=%f)" \
                % (top.length, bottom.length, abs(top.length-bottom.length))
            raise RuntimeError(msg)

        # opposite sides should add up to zero length vector
        for (i,num) in zip(('x', 'y', 'z'), left+right):
            if abs(num) > TOLERANCE:
                msg = "Points not rectangle corners (num[%s]=%f > %f)" \
                                       % (i,num, TOLERANCE)
                raise RuntimeError(msg)

        # Make sure the points are at right angles. Eliminates collinear
        # case too
        dotProd = left.dot(bottom)
        if abs(dotProd) > TOLERANCE:
            msg = " This is not a rectangle (p2-p1)dot(p4-p1) = %f > %f" \
                % (dotProd, TOLERANCE)
            raise RuntimeError(msg)

        self.__center = (p1 + p2 + p3 + p4) / float(Rectangle.NPOINTS)
        self.__calcOrientation(p1, p2, p3, p4)

    def __magnitudeSq(self, first, second):
        """
        Finds the square of the magnitude of the difference of two arrays
        with three elements.
        @param first  The first array
        @param second The second array
        @return  The magnitude squared of (first-second)
        """
        temp = first - second
        return temp.dot(temp)

    def __calcOrientation(self, p1, p2, p3, p4):
        """
        Calculates the orientation matrix for these points.
        @return  The 9 element orientation matrix for these points. 
        """
        # calculate the direction vectors
        xvec =  .5*(p4 + p3) - self.__center
        yvec = -.5*(p1 + p4) + self.__center

        # normalize the vectors
        xvec.normalize()
        yvec.normalize()

        # xvec should change most in x direction
        self.__orient = []
        self.__orient.append(xvec)
        self.__orient.append(yvec)
        self.__orient.append(xvec.cross(yvec))

    def __euler_rotations(self):
        """
        The Euler angles are about the z (alpha), then unrotated y (beta),
        then unrotated z (gamma). This is described in equations and pretty 
        pictures in Arfken pages 199-200.

        George Arfken, Mathematical methods for physicists, 3rd edition
        Academic Press, 1985
        """
        # calculate beta
        beta = getAngle(UNIT_Z.cross(self.__orient[2]).length,
                        UNIT_Z.dot(self.__orient[2]))

        if abs(math.sin(beta)) < TOLERANCE: # special case for numerics
            # since alpha and gamma are coincident, just force gamma to be zero
            gamma = 0.

            # calculate alpha
            cos_beta = UNIT_Z.dot(self.__orient[2])
            if cos_beta == 1. or cos_beta == -1.:
                alpha = getAngle(UNIT_X.dot(self.__orient[1]),
                                 UNIT_Y.dot(self.__orient[1]))
            else:
                raise RuntimeError("Equations aren't worked out for cos(beta)=%f" % cos_beta)

        else: # go with the traditional route
            # calculate alpha
            alpha = getAngle(UNIT_Z.dot(self.__orient[1]),
                             UNIT_Z.dot(self.__orient[0]))

            # calculate gamma
            gamma = getAngle(UNIT_Y.dot(self.__orient[2]),
                             -1.*UNIT_X.dot(self.__orient[2]))

        # output for each: rotation angle (in degrees), axis of rotation
        alpha_rot = [math.degrees(alpha), (0., 0., 1.)]
        beta_rot  = [math.degrees(beta),  (0., 1., 0.)]
        gamma_rot = [math.degrees(gamma), (0., 0., 1.)]
        return (alpha_rot, beta_rot, gamma_rot)

    center = property(lambda self: self.__center[:])
    orientation = property(lambda self: self.__orient[:])
    euler_rot = property(__euler_rotations)
