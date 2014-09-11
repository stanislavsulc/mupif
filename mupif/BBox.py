# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

debug = 0

class BBox:
    """
    Represents an axis aligned bounding box - a rectange in 2d and prism in 3d. 
    Its geometry is described using two points - lover left and upper right.
    The bounding box class provides fast and efficient  methods for testing whether
    point is inside and whether intersection with other bbox exist.
    """
    def __init__(self, coords_ll, coords_ur):
        """Constructor.

        coords_ll -- tuple with coordinates of lower left corner
        coords_ur -- tuple with coordinates of uper right corner
        """
        self.coords_ll = coords_ll
        self.coords_ur = coords_ur
        
    def __str__ (self):
        """ Defines a __str__ method, Python will call it when you call str() or print
        """
        return "BBox ["+str(self.coords_ll)+"-"+str(self.coords_ur)+"]"

    def containsPoint (self, point):
        """
        Returns true if point inside receiver.
        """
        for l, u, x in zip (self.coords_ll, self.coords_ur, point):
            if (x<l or x>u):
                return False
        return True

    def intersects (self, bbox):
        """ 
        Returns true if receiver intersects given bounding box.
        """
        nsd = len(self.coords_ll)
        for i in range(nsd):
            maxleft = max(self.coords_ll[i], bbox.coords_ll[i])
            minright= min(self.coords_ur[i], bbox.coords_ur[i])
            if maxleft > minright: 
                return False
        return True


    def merge (self, entity):
        """
        merges receiver with given entity (position or bbox)
        """
        nsd = len(self.coords_ll)
        if isinstance(entity, BBox):
            # merge with given bbox
            for i in range(nsd):
                self.coords_ll[i]=min(self.coords_ll[i], entity.coords_ll[i])
                self.coords_ur[i]=max(self.coords_ur[i], entity.coords_ur[i])
        else:
            # merge with given coordinates
            for i in range(nsd):
                self.coords_ll[i]=min(self.coords_ll[i], entity[i])
                self.coords_ur[i]=max(self.coords_ur[i], entity[i])