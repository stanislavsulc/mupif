
useAstropy=False

if not useAstropy:
    from .physics.physicalquantities import PhysicalUnit as Unit
    from .physics.physicalquantities import PhysicalQuantity as Quantity
    from .physics.physicalquantities import U
    Q=U
    from .physics.physicalquantities import findUnit, makeQuantity
    QuantityField=Quantity
else:
    import astropy.units as au
    import numpy as np
    from astropy.units import Unit
    from astropy.units import Quantity
    Quantity.inUnitsOf=Quantity.to
    Quantity.getValue=lambda self: self.value
    Quantity.getUnitName=lambda self: self.unit.to_string()
    Quantity.inBaseUnits=lambda self: Quantity.si
    def isCompatible(u1,u2):
        try:
            u1.to(u2)
            return True
        except: return False
    au.UnitBase.isCompatible=isCompatible
    au.UnitBase.inUnitsOf=au.UnitBase.to
    Quantity.isCompatible=isCompatible
    def findUnit(unit): return Unit(unit)
    def makeQuantity(val,unit): return Quantity(val,unit)
    dimensionless=au.def_unit('none',1*au.dimensionless_unscaled)
    au.add_enabled_units([dimensionless])


    class UnitProxy(object):
        def __getitem__(self,n): return Unit(n)
        def __getattr__(self,n): return Unit(n)
    U=Q=UnitProxy()

    def Quantity_validate(cls,v):
        if isinstance(v,Quantity): return v
        raise TypeError(f'Quantity instance required (not a {v.__class__.__name__})')
    @classmethod
    def Quantity_get_validators(cls): yield Quantity_validate
    Quantity.__get_validators__=Quantity_get_validators

    def Unit_validate(cls,v):
        if isinstance(v,au.UnitBase): return v
        raise TypeError(f'Unit instance required (not a {v.__class__.__name__})')
    @classmethod
    def Unit_get_validators(cls): yield Unit_validate
    Unit.__get_validators__=Unit_get_validators


    import Pyro5.api
    Pyro5.api.register_class_to_dict(au.Unit,lambda x: {'__class__':'astropy.units.Unit','unit':x.to_string()})
    Pyro5.api.register_dict_to_class('astropy.units.Unit',lambda cname,x: au.Unit(x['unit']))
    Pyro5.api.register_class_to_dict(au.Quantity,lambda x: {'__class__':'astropy.units.Quantity','value':np.array(x.value).tolist(),'unit':x.unit.to_string()})
    Pyro5.api.register_dict_to_class('astropy.units.Quantity',lambda cname,x: au.Quantity(x['value'],au.Unit(x['unit'])))
