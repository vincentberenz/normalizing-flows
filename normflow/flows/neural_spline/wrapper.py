from torch import nn

from ..base import Flow

from .coupling import PiecewiseRationalQuadraticCoupling
from .autoregressive import MaskedPiecewiseRationalQuadraticAutoregressive
from ...nets.resnet import ResidualNet
from ...utils.masks import create_alternating_binary_mask



class CoupledRationalQuadraticSpline(Flow):
    """
    Neural spline flow coupling layer, wrapper for the implementation
    of Durkan et al., see https://github.com/bayesiains/nsf
    """
    def __init__(
            self,
            num_input_channels,
            num_blocks,
            num_hidden_channels,
            num_bins=8,
            tail_bound=3,
            activation=nn.ReLU,
            dropout_probability=0.,
            reverse_mask=False
    ):
        """
        Constructor
        :param num_input_channels: Flow dimension
        :type num_input_channels: Int
        :param num_blocks: Number of residual blocks of the parameter NN
        :type num_blocks: Int
        :param num_hidden_channels: Number of hidden units of the NN
        :type num_hidden_channels: Int
        :param num_bins: Number of bins
        :type num_bins: Int
        :param tail_bound: Bound of the spline tails
        :type tail_bound: Int
        :param activation: Activation function
        :type activation: torch module
        :param dropout_probability: Dropout probability of the NN
        :type dropout_probability: Float
        :param reverse_mask: Flag whether the reverse mask should be used
        :type reverse_mask: Boolean
        """
        super().__init__()
        self.reverse = reverse

        def transform_net_create_fn(in_features, out_features):
            return ResidualNet(
                in_features=in_features,
                out_features=out_features,
                context_features=None,
                hidden_features=num_hidden_channels,
                num_blocks=num_blocks,
                activation=activation(),
                dropout_probability=dropout_probability,
                use_batch_norm=False
            )

        self.prqct=PiecewiseRationalQuadraticCoupling(
            mask=create_alternating_binary_mask(
                num_input_channels,
                even=reverse_mask
            ),
            transform_net_create_fn=transform_net_create_fn,
            num_bins=num_bins,
            tails='linear',
            tail_bound=tail_bound,

            # Setting True corresponds to equations (4), (5), (6) in the NSF paper:
            apply_unconditional_transform=True
        )

    def forward(self, z):
        z, log_det = self.prqct.inverse(z)
        return z, log_det.view(-1)

    def inverse(self, z):
        z, log_det = self.prqct(z)
        return z, log_det.view(-1)


class AutoregressiveRationalQuadraticSpline(Flow):
    """
    Neural spline flow coupling layer, wrapper for the implementation
    of Durkan et al., see https://github.com/bayesiains/nsf
    """
    def __init__(
            self,
            num_input_channels,
            num_blocks,
            num_hidden_channels,
            num_bins=8,
            tail_bound=3,
            activation=nn.ReLU,
            dropout_probability=0.
    ):
        """
        Constructor
        :param num_input_channels: Flow dimension
        :type num_input_channels: Int
        :param num_blocks: Number of residual blocks of the parameter NN
        :type num_blocks: Int
        :param num_hidden_channels: Number of hidden units of the NN
        :type num_hidden_channels: Int
        :param num_bins: Number of bins
        :type num_bins: Int
        :param tail_bound: Bound of the spline tails
        :type tail_bound: Int
        :param activation: Activation function
        :type activation: torch module
        :param dropout_probability: Dropout probability of the NN
        :type dropout_probability: Float
        """
        super().__init__()
        self.reverse = reverse

        self.mprqat=MaskedPiecewiseRationalQuadraticAutoregressive(
            features=num_input_channels,
            hidden_features=num_hidden_channels,
            context_features=None,
            num_bins=num_bins,
            tails='linear',
            tail_bound=tail_bound,
            num_blocks=num_blocks,
            use_residual_blocks=True,
            random_mask=False,
            activation=activation(),
            dropout_probability=dropout_probability,
            use_batch_norm=False)

    def forward(self, z):
        z, log_det = self.mprqat.inverse(z)
        return z, log_det.view(-1)

    def inverse(self, z):
        z, log_det = self.mprqat(z)
        return z, log_det.view(-1)