import type { OrderStatus } from '../types'

const MAP: Record<OrderStatus, string> = {
  FILLED:           'badge-filled',
  NEW:              'badge-new',
  PARTIALLY_FILLED: 'badge-partial',
  CANCELED:         'badge-canceled',
  REJECTED:         'badge-rejected',
  EXPIRED:          'badge-canceled',
}

export default function StatusBadge({ status }: { status: OrderStatus }) {
  return (
    <span className={MAP[status] ?? 'badge-canceled'}>
      <span className="w-1.5 h-1.5 rounded-full bg-current inline-block" />
      {status.replace('_', ' ')}
    </span>
  )
}
