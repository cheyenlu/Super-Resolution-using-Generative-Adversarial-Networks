from keras import backend as K
from keras.regularizers import ActivityRegularizer
import numpy as np

dummy_loss_val = K.variable(0.0)

softminus = lambda x: x - K.softplus(x)

# Dummy loss function which simply returns 0
# This is because we will be training the network using regularizers.
def dummy_loss(y_true, y_pred):
    return dummy_loss_val


def psnr(y_true, y_pred):
    assert y_true.shape == y_pred.shape, "Cannot calculate PSNR. Input shapes not same." \
                                         " y_true shape = %s, y_pred shape = %s" % (str(y_true.shape),
                                                                                   str(y_pred.shape))

    return -10. * np.log10(np.mean(np.square(y_pred - y_true)))

def PSNRLoss(y_true, y_pred):
    """
    PSNR is Peek Signal to Noise Ratio, which is similar to mean squared error.

    It can be calculated as
    PSNR = 20 * log10(MAXp) - 10 * log10(MSE)

    When providing an unscaled input, MAXp = 255. Therefore 20 * log10(255)== 48.1308036087.
    However, since we are scaling our input, MAXp = 1. Therefore 20 * log10(1) = 0.
    Thus we remove that component completely and only compute the remaining MSE component.
    """
    return 48.1308036087 - 10. * np.log10(K.mean(K.square(y_pred - y_true)))


class ContentVGGRegularizer(ActivityRegularizer):

    def __init__(self, weight=1.0):
        super(ContentVGGRegularizer, self).__init__()
        self.weight = weight
        self.uses_learning_phase = False

    def __call__(self, x):
        batch_size = K.shape(x)[0] // 2

        generated = x[:batch_size] # Generated by network features
        content = x[batch_size:] # True X input features

        loss = self.weight * K.mean(K.sum(K.square(content - generated)))
        return loss

    def get_config(self):
        return {'name' : self.__class__.__name__,
                'weight' : self.weight}


class AdversarialLossRegularizer(ActivityRegularizer):

    def __init__(self, weight=1e-3):
        super(AdversarialLossRegularizer, self).__init__()
        self.weight = weight
        self.uses_learning_phase = False

    def __call__(self, x):
        gan_outputs = x

        loss = self.weight * K.mean(1 - softminus(gan_outputs))
        return loss

    def get_config(self):
        return {'name' : self.__class__.__name__,
                'weight' : self.weight}


class TVRegularizer(ActivityRegularizer):
    """ Enforces smoothness in image output. """

    def __init__(self, img_width, img_height, weight=2e-8):
        super(TVRegularizer, self).__init__()
        self.img_width = img_width
        self.img_height = img_height
        self.weight = weight
        self.uses_learning_phase = False

    def __call__(self, x):
        assert K.ndim(x) == 4
        if K.image_dim_ordering() == 'th':
            a = K.square(x[:, :, :self.img_width - 1, :self.img_height - 1] - x[:, :, 1:, :self.img_height - 1])
            b = K.square(x[:, :, :self.img_width - 1, :self.img_height - 1] - x[:, :, :self.img_width - 1, 1:])
        else:
            #print "width {} height{} ".format(self.img_width, self.img_height)
            #print "x shape {} {}".format(x.shape[0], x.shape[1])
            a = K.square(x[:, :self.img_width - 1, :self.img_height - 1, :] - x[:, 1:, :self.img_height - 1, :])
            b = K.square(x[:, :self.img_width - 1, :self.img_height - 1, :] - x[:, :self.img_width - 1, 1:, :])
        loss = self.weight * K.mean(K.sum(K.pow(a + b, 1.25)))
        return loss

    def get_config(self):
        return {'name' : self.__class__.__name__,
                'img_width' : self.img_width,
                'img_height' : self.img_height,
                'weight' : self.weight}
