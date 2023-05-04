SYSTEM_EVENT_FLAG = 'S'
STOCK_DIR_FLAG = 'R'
ADD_ORDER_NO_MPID_FLAG = 'A'
ADD_ORDER_FLAG = 'F'
ORDER_EXECUTED_FLAG = 'E'
ORDER_EXECUTED_DIFF_PRICE_FLAG = 'C'
ORDER_REPLACE_FLAG = 'U'
ORDER_DELETE_FLAG = 'D'
TRADE_MSG_FLAG = 'P'
MKT_OPEN_FLAG = 'Q'
MKT_CLOSE_FLAG = 'M'
PRINTABLE = "Y"
TIMESTAMP_FORMAT = '6s'
REPORTING_INTERVAL = 60*60*(10**9)

ITCH_VWAP_MSG_INFO = {
    # System Event Message
    SYSTEM_EVENT_FLAG: dict(
        size=11,
        format='>HH6sc'
    ),
    # Stock Directory
    STOCK_DIR_FLAG: dict(
        size=38,
        format='>HH6s8sccIcc2scccccIc'
    ),
    # Add Order – No MPID Attribution
    ADD_ORDER_NO_MPID_FLAG: dict(
        size=35,
        format='>HH6sQcI8sI'
    ),
    # Add Order with MPID Attribution
    ADD_ORDER_FLAG: dict(
        size=39,
        format='>HH6sQcI8sI4s'
    ),
    # Order Executed Message
    ORDER_EXECUTED_FLAG: dict(
        size=30,
        format='>HH6sQIQ'
    ),
    # Order Executed With Price Message
    ORDER_EXECUTED_DIFF_PRICE_FLAG: dict(
        size=35,
        format='>HH6sQIQcI'
    ),
    # Order Replace Message
    ORDER_REPLACE_FLAG: dict(
        size=34,
        format='>HH6sQQII'
    ),
    # Order Delete Message
    ORDER_DELETE_FLAG: dict(
        size=18,
        format='>HH6sQ'
    ),
    # Trade Message (Non-Cross)
    TRADE_MSG_FLAG: dict(
        size=43,
        format='>HH6sQcIQIQ'
    )
}

ITCH_NON_VWAP_MSG_INFO = dict(
    H=dict(size=24), Y=dict(size=19), L=dict(size=25), V=dict(size=34),
    W=dict(size=11), K=dict(size=27), J=dict(size=34), h=dict(size=20),
    X=dict(size=22), Q=dict(size=39), B=dict(size=18), I=dict(size=49),
    N=dict(size=19)
)
