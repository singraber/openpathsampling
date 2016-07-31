import openpathsampling as paths
import openpathsampling.netcdfplus as netcdfplus

class InterfaceSet(netcdfplus.StorableNamedObject):
    """List of volumes representing a set of interfaces, plus metadata.

    Parameters
    ----------
    volumes : list of :class:`.Volume`
        volumes representing the interfaces
    cv : :class:`.CollectiveVariable`
        order parameter for this interface set
    lambdas : list
        values associated with the CV at each interface
    """
    def __init__(self, volumes, cv=None, lambdas=None):
        self.volumes = volumes
        self.cv = cv
        self.lambdas = lambdas
        try:
            self.direction = lambdas[-1] >= lambdas[0]
        except TypeError:
            self.direction = 0

        vlambdas = lambdas
        if vlambdas is None:
            vlambdas = [None]*len(volumes)
        self._lambda_dict = {vol: lmbda 
                             for (vol, lmbda) in zip(volumes, vlambdas)}

    def get_lambda(self, volume):
        """Lambda (value of the CV) associated with a given interface volume

        Parameters
        ----------
        volume : :class:`.Volume`
            the interface volume

        Returns
        -------
        float or int
            the value of the CV associated with the interface
        """
        return self._lambda_dict[volume]

    def __len__(self):
        return len(self.volumes)

    def __getitem__(self, key):
        return self.volumes[key]

    def __iter__(self):
        return iter(self.volumes)

    def __contains__(self, item):
        return item in self.volumes

    def __reversed__(self):
        return self.volumes.__reversed__()


class GenericVolumeInterfaceSet(InterfaceSet):
    """Abstract class for InterfaceSets for CVRange-based volumes
    """
    def __init__(self, cv, minvals, maxvals, intersect_with, volume_func):
        if intersect_with is None:
            intersect_with = paths.FullVolume()
        self.intersect_with = intersect_with

        direction = self._determine_direction(minvals, maxvals)
        minvs, maxvs = self._prep_minvals_maxvals(minvals, maxvals,
                                                  direction)
        lambdas = {1: maxvs, -1: minvs, 0: None}[direction]
        volumes = [self.intersect_with & volume_func(minv, maxv)
                   for (minv, maxv) in (minvs, maxvs)]
        super(self, GenericVolumeInterfaceSet).__init__(volumes, cv, lambdas)

        if direction == 0:
            self.volume_func = volume_func
        elif direction > 0:
            self.volume_func = lambda maxv : volume_func(minvals, maxv)
        elif direction < 0:
            self.volume_func = lambda minv : volume_func(minv, maxvals)

    @staticmethod
    def _determine_direction(minvals, maxvals):
        try:
            len_min = len(minvals)
        except TypeError:
            len_min = 1
        try:
            len_max = len(maxvals)
        except TypeError:
            len_max = 1
        if len_min == len_max:
            result = 0
            # check if all elements of each list matches its first element
            if len_min > 1 and minvals.count(minvals[0]) == len_min:
                result += 1
            if len_max > 1 and maxvals.count(maxvals[0]) == len_max:
                result += -1
            # this approach means that if multiple vals are equal (for some
            # drunken reason, you decided to have a bunch of equivalent
            # volumes?) we return that we can't tell the direction
            return result
        elif len_max > len_min == 1:
            return 1
        elif len_min > len_max == 1:
            return -1
        else:
            raise RuntimeError("Can't reconcile array lengths: " 
                               + str(minvals) + ", " + str(maxvals))
                        

    @staticmethod
    def _prep_minvals_maxvals(minvals, maxvals, direction):
        minvs = minvals
        maxvs = maxvals
        if direction > 0:
            minvs = [minvs]*len(maxvs)
        elif direction < 0:
            maxvs = [maxvs]*len(maxvs)
        return minvs, maxvs

    def new_interface(self, lambda_i):
        return self.intersect_with & self.volume_func(lambda_i)


class VolumeInterfaceSet(GenericVolumeInterfaceSet):
    def __init__(self, cv, minvals, maxvals, intersect_with=None):
        volume_func = lambda minv, maxv: paths.CVRangeVolume(cv, minv, maxv)
        super(self, VolumeInterfaceSet).__init__(cv, minvals, maxvals,
                                                 intersect_with,
                                                 volume_func)


class PeriodicVolumeInterfaceSet(GenericVolumeInterfaceSet):
    def __init__(self, cv, minvals, maxvals, period_min=None,
                 period_max=None, intersect_with=None):
        volume_func = lambda minv, maxv: paths.CVRangeVolumePeriodic(
            cv, minv, maxv, period_min, period_max
        )
        super(self, VolumeInterfaceSet).__init__(cv, minvals, maxvals,
                                                 intersect_with,
                                                 volume_func)


